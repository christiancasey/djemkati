from psd_tools import *
from PIL import Image
import cv2
import numpy as np
import os
import re

from .LineGlyph import *
import Sobti.models as m

from django.core.files import File
from django.conf import settings
# from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO     # for handling byte strings
# from io import StringIO    # for handling unicode strings

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

# Extract the layers from the PSD image and save them as separate PNG's
def ExtractLayers(page):
    """Extract the layers from the input PSD and save them to disk
    
    Parameters:
    page (Django db object)"""
    
    ClearPageObjects(page)
    
    fPsd = page.image
    
    PrepareDirectory(os.path.split(fPsd.path)[0], 'layers')
    
    sPath, _ = os.path.split(fPsd.path)
    imPsd = PSDImage.open(fPsd.open())
    
    if len(imPsd) < 1:
    	raise Exception('Not enough layers in image: ' + fPsd.name)

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
            	raise Exception('Layers are not RGB images: ' + fPsd.name)
            
            # Find places where any channel differs from the others (i.e. color)
            mLayer = np.uint8( (mLayer[:,:,0] != mLayer[:,:,1]) | (mLayer[:,:,1] != mLayer[:,:,2]) )*255
            imLayer = Image.fromarray(cv2.cvtColor(mLayer, cv2.COLOR_GRAY2RGB))
        
        # Save the image to disk and into the database
        sRelFilename = os.path.join(os.path.split(fPsd.name)[0], 'layers', '{0:02d}.png'.format(i+1))
        dbLayer = page.layer_set.create(number=i+1, image=DjangoImage(imLayer, sRelFilename))
        

def AnalyzeManuscript(page):
    """Analyze input text image and generate manuscript object
    
    Parameters:
    page (Django db object)"""
    
    fPsd = page.image
    
    # # Clear all the sub objects in the page
    # for dbLine in page.line_set.all():
    #   dbLine.delete()
    
    PrepareDirectory(os.path.split(fPsd.path)[0], 'lines')
    PrepareDirectory(os.path.split(fPsd.path)[0], 'glyphs')
    
    # Layers contain lines?
    vIsLine = [ False, True, True, False, False, False ]
    
    # Generate ManuscriptCollection object from layers
    dbLayers = page.layer_set.order_by('number')
    
    # Start with the background text layer
    imManuscript = cv2.imread(dbLayers[0].image.path)
    vManuscript = ManuscriptCollection(fPsd.name, imManuscript)
    
    # Add region mask layers to the ManuscriptCollection
    for i in range(1,6):
        img = cv2.imread(dbLayers[i].image.path, cv2.IMREAD_GRAYSCALE)
        vManuscript.populate(img, vIsLine[i])
        
    # Finalize sorting of lines and glyphs
    vManuscript.organize_components()
        
    # Line regions in the facsimile
    iGlyphInPage = 0 # Glyph counter for entire page
    for i, line in enumerate(vManuscript.get_line_list()):
        
        sRelFilename = os.path.join(os.path.split(fPsd.name)[0], 'lines', '{0:03d}.png'.format(i+1))
        imLine = Image.fromarray(cv2.cvtColor(line.text_image, cv2.COLOR_RGBA2BGRA))
        dbLine = page.line_set.create(number_in_page=i+1, image=DjangoImage(imLine, sRelFilename))
        
        vPoly = dbLine.polygon_set.create(polygon_type='line', glyph=None,
                x_min=line.Xmin, y_min=line.Ymin, x_max=line.Xmax, y_max=line.Ymax, 
                x_cent=line.Xc, y_cent=line.Yc)
        for iPt in range(line.polygon.shape[0]):
            vI = line.polygon[iPt,:]
            vPoly.polygonpoint_set.create(x_coordinate=vI[0],y_coordinate=vI[1],t_coordinate=iPt+1)
        
        # Glyph regions in each line in the facsimile
        for j, glyph in enumerate(vManuscript.get_glyphs_by_line(line)):
            iGlyphInPage += 1
            
            sRelFilename = os.path.join(os.path.split(fPsd.name)[0], 'glyphs', '{0:03d}_'.format(i+1) + '{0:04d}.png'.format(j+1))
            imGlyph = Image.fromarray(cv2.cvtColor(glyph.text_image, cv2.COLOR_RGBA2BGRA))
            dbGlyph = dbLine.glyph_set.create(number_in_line=j+1, number_in_page=iGlyphInPage, image=DjangoImage(imGlyph, sRelFilename))
            
            vPoly = dbGlyph.polygon_set.create(polygon_type='glyph',line=dbLine,
                    x_min=glyph.Xmin, y_min=glyph.Ymin, x_max=glyph.Xmax, y_max=glyph.Ymax, 
                    x_cent=glyph.Xc, y_cent=glyph.Yc)
            for iPt in range(glyph.polygon.shape[0]):
                vI = glyph.polygon[iPt,:]
                vPoly.polygonpoint_set.create(x_coordinate=vI[0],y_coordinate=vI[1],t_coordinate=iPt+1)
            
def GetObjectPolygon(dbObj,sType='line'):
    vPolygon = []
    if not dbObj is None:
        v = dbObj.polygon_set.filter(polygon_type=sType)
        if len(v) == 1:
            v = v[0].polygonpoint_set.order_by('t_coordinate')
            for point in v:
                vPolygon = vPolygon + [[point.x_coordinate, point.y_coordinate ]]
    
    return vPolygon
    

def PrepareDirectory(sPath, sDir):
    sPathDir = os.path.join(sPath, sDir)
    if not os.path.exists(sPathDir):
        os.mkdir(sPathDir)
    
    RemoveDirectoryContents(sPathDir)
        
def RemoveDirectoryContents(dir_to_search):
    for dirpath, dirnames, filenames in os.walk(dir_to_search, topdown=False):
        for filename in filenames:
            try:
                os.remove(os.path.join(dirpath, filename))
            except OSError as ex:
                pass
        
        for dirname in dirnames:
            try:
                os.rmdir(os.path.join(dirpath, dirname))
            except OSError as ex:
                pass

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

