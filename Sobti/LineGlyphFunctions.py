from psd_tools import *
from PIL import Image
import cv2
import numpy as np
import os
import shutil
import re
import time

from .LineGlyph import *
import Sobti.models as m

from django.core.files import File
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry, LineString, Point

# from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO	 # for handling byte strings
# from io import StringIO	# for handling unicode strings

# from django.db import models
# from django.core.files.base import ContentFile
# from django.core.files.storage import default_storage as storage
# from django.db import models

# Constants
THUMBNAIL_HEIGHT = 64

# Simple helper to convert a PIL image into the file for the database
def DjangoImage(img, sName, format='PNG'):
	
	# Delete the old file to avoid a Django renaming
	try:
		os.remove(os.path.join(settings.BASE_DIR, settings.MEDIA_ROOT, sName))
	except OSError as ex:
		pass
	
	img_io = BytesIO()
	img.save(img_io, format)
	img_content = File(img_io, name=sName)
	return img_content

def ImagePreviewName(sName):
	sName, _ = os.path.splitext(sName)
	return os.path.join(sName + '.png')

def ImageThumbnailName(sName):
	sName, _ = os.path.splitext(sName)
	return os.path.join(sName + '_thumb.png')
	
# Get a composite png image of the master psd for display purposes
def ImagePreview(fPsd):
	imPsd = PSDImage.open( fPsd.open() )
	
	# Save a png for display
	imComposite = imPsd.composite()
	return DjangoImage(imComposite, ImagePreviewName(fPsd.name))

# Get a composite png image of the master psd for display purposes
def ImageThumbnail(fPsd):
	imPsd = PSDImage.open( fPsd.open() )
	
	if len(imPsd) > 0:
		imThumbnail = imPsd[0].composite()
		iWidth, iHeight = imThumbnail.size
		imThumbnail = imThumbnail.resize((np.uint32(np.ceil(THUMBNAIL_HEIGHT/iHeight*iWidth)), THUMBNAIL_HEIGHT))
		return DjangoImage(imThumbnail, ImageThumbnailName(fPsd.name))
	
	return None

def ClearPageObjects(dbPage):
	"""Clean out any existing sub objects for the given page
	This includes layers, line and glyph regions, polygons, etc.
	
	Parameters:
	dbPage (Django db object)"""
	
	for dbLayer in dbPage.layer_set.all():
		dbLayer.delete()
	for dbLine in dbPage.line_set.all():
		dbLine.delete()

# Get everything set up on the server for working with the image
def PrepImageData(page):
	
	# Move the page image to the proper directory
	sOldName = page.image.name
	sNewPath = GetPageDataPath(page)
	sNewName = os.path.join(sNewPath, 'page.psd')
	
	# Skip it if nothing will change anyway
	if sOldName != sNewName:
		
		sNewPathFull = os.path.join(settings.BASE_DIR, settings.MEDIA_ROOT, sNewPath)
		if not os.path.exists(sNewPathFull):
			os.makedirs(sNewPathFull)
	
		os.rename(
			os.path.join(settings.BASE_DIR, settings.MEDIA_ROOT, sOldName),
			os.path.join(settings.BASE_DIR, settings.MEDIA_ROOT, sNewName)
		)
		page.image.name = sNewName
		page.save()
	
	# Create an image preview (if necessary)
	if page.image_preview is None \
		or not page.image_preview.name == ImagePreviewName(page.image.name):
		
		page.image_preview = ImagePreview(page.image)
		page.save()
	
	# Create an image thumbnail (if necessary)
	if page.image_thumbnail is None \
		or not page.image_thumbnail.name == ImageThumbnailName(page.image.name):

		page.image_thumbnail = ImageThumbnail(page.image)
		page.save()
	
	# Delete all of the old sub-part images (glyphs, lines, layers)
	vDir = ['glyphs', 'lines', 'layers']
	for sDir in vDir:
		sDirPath = os.path.join(settings.BASE_DIR, settings.MEDIA_ROOT, sNewPath, sDir)
		if os.path.exists(sDirPath):
			shutil.rmtree(sDirPath)
			
	ClearPageObjects(page)
	
	return True

# Extract the layers from the PSD image and save them as separate PNG's
def ExtractLayers(page):
	"""Extract the layers from the input PSD and save them to disk
	
	Parameters:
	page (Django db object)"""
	
	fPsd = page.image
	sPath, _ = os.path.split(fPsd.path)
	PrepareDirectory(os.path.join(sPath, 'layers'))
	
	imPsd = PSDImage.open(fPsd.open())
	
	if len(imPsd) < 1:
		return False
		# raise Exception('Not enough layers in image: ' + fPsd.name)

	vViewport = imPsd[0].bbox
	for i, layer in enumerate(imPsd):
		
		# Save each layer at the original image size so everything lines up
		layer.opacity = 255;
		imLayer = layer.composite(viewport=vViewport, force=True)
	
		# Modify the higher layers
		if i > 0:
			# Mark the places where there is any color in the layers
			# These are the marked regions for lines and glyphs
			mLayer = np.array(imLayer)
			
			# Deal with images that are not RGB
			if len( mLayer.shape ) < 3 or mLayer.shape[2] < 3:
				return False
				# raise Exception('Layers are not RGB images: ' + fPsd.name)
			
			# Find places where any channel differs from the others (i.e. color)
			mLayer = np.uint8( (mLayer[:,:,0] != mLayer[:,:,1]) | (mLayer[:,:,1] != mLayer[:,:,2]) )*255
			imLayer = Image.fromarray(cv2.cvtColor(mLayer, cv2.COLOR_GRAY2RGB))
		
		# Save the image to disk and into the database
		sRelFilename = os.path.join(os.path.split(fPsd.name)[0], 'layers', '{0:02d}.png'.format(i+1))
		dbLayer = page.layer_set.create(number=i+1, image=DjangoImage(imLayer, sRelFilename))
	
	return True

# Extract the lines from the manuscript page
def AnalyzeManuscript(page):
	"""Analyze input text image and generate manuscript object
	
	Parameters:
	page (Django db object)"""
	
	fPsd = page.image
	sPath, _ = os.path.split(fPsd.path)
	sPathAbs, _ = os.path.split(fPsd.name)
	
	PrepareDirectory(os.path.join(sPath, 'lines'))
	PrepareDirectory(os.path.join(sPath, 'glyphs'))
	
	# Layers contain lines?
	vIsLine = [ False, True, True, False, False, False ]
	
	# Generate ManuscriptCollection object from layers
	dbLayers = page.layer_set.order_by('number')
	
	# Start with the background text layer
	imManuscript = cv2.imread(dbLayers[0].image.path)
	vManuscript = ManuscriptCollection(fPsd.name, imManuscript)
	
	print('Before anything, horz: ' + str(vManuscript.horz))
	
	# Add line mask layers to the ManuscriptCollection
	for i in range(1,6):
		if vIsLine[i]:
			print('layer %i' % (i+1))
			img = cv2.imread(dbLayers[i].image.path, cv2.IMREAD_GRAYSCALE)
			vManuscript.populate(img, vIsLine[i])
	
	print('After lines, before glyphs, horz: ' + str(vManuscript.horz))
	
	# Add glyph mask layers to the ManuscriptCollection
	for i in range(1,6):
		if not vIsLine[i]:
			print('layer %i' % (i+1))
			img = cv2.imread(dbLayers[i].image.path, cv2.IMREAD_GRAYSCALE)
			vManuscript.populate(img, vIsLine[i])
	
	print('After glyphs and lines, before organize, horz: ' + str(vManuscript.horz))
	
	# Finalize sorting of lines and glyphs
	vManuscript.organize_components()
	print('After glyphs, lines, and organize, horz: ' + str(vManuscript.horz))
	
	
	# Line regions in the facsimile
	iGlyphInPage = 0 # Glyph counter for entire page
	vPolyPoints = []
	for i, line in enumerate(vManuscript.get_line_list()):
		
		print('For line in vMS, i=%i' % i)
		print(os.path.split(fPsd.name)[0] + '----' + sPathAbs)
		
		
		time_zero = time.time()
		
		# # Print out a np array so that it can be used as input
		# for p in line.polygon:
		# 	print('[%i, %i],' % tuple(p))
		
		lsShape = LineString(line.polygon)
		if len(lsShape) > 0 and not lsShape.closed:
			lsShape.append(lsShape[0])
		
		print(line.polygon[0])
		print(lsShape)
		print(lsShape.closed)
		
		sRelFilename = os.path.join(sPathAbs, 'lines', '{0:03d}.png'.format(i+1))
		imLine = Image.fromarray(cv2.cvtColor(line.text_image, cv2.COLOR_RGBA2BGRA))
		dbLine = page.line_set.create(number_in_page=i+1, image=DjangoImage(imLine, sRelFilename), shape=lsShape)
		
		
		
		# Glyph regions in each line in the facsimile
		for j, glyph in enumerate(vManuscript.get_glyphs_by_line(line)):
			iGlyphInPage += 1
			
			lsShape = LineString(glyph.polygon)
			if len(lsShape) > 0 and not lsShape.closed:
				lsShape.append(lsShape[0])
			
			sRelFilename = os.path.join(sPathAbs, 'glyphs', '{0:03d}_'.format(i+1) + '{0:04d}.png'.format(j+1))
			imGlyph = Image.fromarray(cv2.cvtColor(glyph.text_image, cv2.COLOR_RGBA2BGRA))
			dbGlyph = dbLine.glyph_set.create(number_in_line=j+1, number_in_page=iGlyphInPage, image=DjangoImage(imGlyph, sRelFilename), shape=lsShape)
			
			# vPoly = dbGlyph.polygon_set.create(polygon_type='glyph', line=dbLine,
			# 		x_min=glyph.Xmin, y_min=glyph.Ymin, x_max=glyph.Xmax, y_max=glyph.Ymax, 
			# 		x_cent=glyph.Xc, y_cent=glyph.Yc)
			# 
			# for iPt in range(glyph.polygon.shape[0]):
			# 	vI = glyph.polygon[iPt,:]
			# 	# vPoly.polygonpoint_set.create(x_coordinate=vI[0],y_coordinate=vI[1],t_coordinate=iPt+1)
			# 	vPolyPoint = m.PolygonPoint(polygon=vPoly,x_coordinate=vI[0],y_coordinate=vI[1],t_coordinate=iPt+1)
			# 	vPolyPoints.append(vPolyPoint)
			# 
			# print('Time elapsed: %f' % (time.time()-time_zero))
			# time_zero = time.time()
	
	m.PolygonPoint.objects.bulk_create(vPolyPoints)
	print('Time elapsed: %f' % (time.time()-time_zero))
	time_zero = time.time()
		
	return True

def PageProcess(page):
	sError = None
	bSuccess = True
	
	time_zero = time.time()
	print('Prepping image data...')
	bSuccess = bSuccess and PrepImageData(page)
	if not bSuccess:
		sError = 'Error storing image data on server'
	print('Prepping image data: Time elapsed: %f' % (time.time()-time_zero))
	time_zero = time.time()
	
	print('Extracting layers...')
	bSuccess = bSuccess and ExtractLayers(page)
	if not bSuccess:
		sError = 'Error splitting page into layers'
	print('Extracting layers: Time elapsed: %f' % (time.time()-time_zero))
	time_zero = time.time()
	
	
	print('Analyzing manuscript...')
	bSuccess = bSuccess and AnalyzeManuscript(page)
	if not bSuccess:
		sError = 'Error analyzing lines and glyphs in page'
	print('Analyzing manuscript: Time elapsed: %f' % (time.time()-time_zero))
	time_zero = time.time()
	
	
	if not bSuccess:
		shutil.rmtree(GetPageDataPath(page,True))
		page.delete()
	
	return sError

def GetObjectPolygon(dbObj,sType='line'):
	vPolygon = []
	if not dbObj is None:
		vPolygon = [list(xy) for xy in dbObj.shape]
	
	return vPolygon
	

def PrepareDirectory(sPath, sDir=None):
	# Deal with the two different ways this function is used
	if sDir is None:
		sSubDir = sPath
	else:
		sSubDir = os.path.join(sPath,sDir)
		
	if os.path.isdir(sSubDir):
		shutil.rmtree(sSubDir)
	os.mkdir(sSubDir)

def iris(m):
	"""Rainbow colored colormap. 
	Similar to Jet and HSV, but changes smoothly.
	As a result, it has few brightness peaks and looks much less harsh.
	It was created using data from photos of rainbows.

	Parameters:
	m (int): number of color values in map

	Returns:
	3xm numpy array of RGB color values
	"""
	fPurple = 2*np.pi/3
	vCM = np.zeros([m,3])
	for i in range(m):
		fTh = ((m-i)/m) * (np.pi*2 - fPurple)
		vCM[i,:] = [ (np.cos(fTh)+1)/2, (np.cos(fTh-2*np.pi/3)+1)/2, (np.cos(fTh-4*np.pi/3)+1)/2 ]
	return vCM


# Pass a page object to get the path for its data on the server
def GetPageDataPath(page, bFull = False):
	sPath = os.path.join(
		'{0:06d}'.format(page.manuscript.text.id), 
		'{0:06d}'.format(page.manuscript.id), 
		'{0:06d}'.format(page.id))
	if not bFull:
		return sPath
	return os.path.join(settings.BASE_DIR, settings.MEDIA_ROOT,sPath)