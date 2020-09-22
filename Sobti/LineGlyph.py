import cv2
import numpy as np
from scipy import ndimage
from skimage.color import label2rgb
from skimage.measure import label, regionprops, regionprops_table
import os

################################################################################
# REGION (SUPER)
################################################################################
class Region:
	"""Region:
	a super class for line- and glyph-type regions in the facsimile image"""
	
	def __init__(self, mask, text_image = None):
		
		self.mask = np.uint8( mask > 0 )*255
		self._horz = None
		self._horz_vote = None
		
		prop = regionprops(mask)[0]
		self.Yc, self.Xc = prop.centroid
		self.Ymin, self.Xmin, self.Ymax, self.Xmax = prop.bbox 
		
		
		edges = cv2.Canny(mask,30,200)
		edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT,(4,4)))
		contour, _ = cv2.findContours(edges,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
		self.polygon = cv2.approxPolyDP(contour[0],2,True)
		self.polygon = np.squeeze(self.polygon)
		
		if not text_image is None:
			self.text_image = text_image[self.Ymin:self.Ymax,self.Xmin:self.Xmax,:]
			
			imMaskBox = self.mask[self.Ymin:self.Ymax,self.Xmin:self.Xmax]
			self.text_image = cv2.bitwise_and(self.text_image, cv2.cvtColor(imMaskBox, cv2.COLOR_GRAY2RGB))
			
			#Create alpha channel to show only polygon region
			self.text_image = np.dstack((self.text_image, imMaskBox))
			
			# self.text_image = Image.fromarray(self.text_image)
	
	@property
	def horz(self):
		return self._horz
	
	@horz.setter
	def horz(self, val):
		self._horz = val
	
	def overlap(self, other):
		return np.sum( np.multiply( self.mask, other.mask ) )


################################################################################
# LINE REGION
################################################################################
class LineRegion(Region):
	"""LineRegion:
	a sub class for line-type regions in the facsimile image"""
	
	def __init__(self, mask, text_image = None):
		super(LineRegion, self).__init__(mask, text_image)
		
		self._horz_vote = (self.Xmax-self.Xmin) > (self.Ymax-self.Ymin)
		Region.horz.fset(self, self._horz_vote)
		
		self.glyphs = list()
		
	def __lt__(self, other):
		if Region.horz.fget(self):
			return self.Yc < other.Yc
		else:
			return self.Xc > other.Xc

	@property
	def horz_vote(self):
		return self._horz_vote
	
		
################################################################################
# GLYPH REGION
################################################################################
class GlyphRegion(Region):
	"""GlyphRegion:
	a sub class for glyph-type regions in the facsimile image"""
	
	def __init__(self, mask, text_image = None):
		super(GlyphRegion, self).__init__(mask, text_image)
		self.line = None
	
	def __lt__(self, other):
		# print(Region.horz.fget(self))
		if Region.horz.fget(self):
			return self.Xc > other.Xc
		else:
			return self.Yc < other.Yc
			
################################################################################
# MANUSCRIPT
################################################################################
class ManuscriptCollection(object):
	"""ManuscriptCollection:
	a collection of regions in the facsimile,
	organized and sorted based on the orientation of the text"""
	
	def __init__(self, image_filename, text_image):
		self.image_filename = image_filename
		self.text_image = text_image
		self.lines = list()
		self.glyphs = list()
		self._horz = None
		
	@property
	def horz(self):
		self.vote_on_orientation()
		return self._horz
	
	@horz.setter
	def horz(self, val):
		self._horz = val
		for reg in self.lines:
			reg.horz = self._horz
		for reg in self.glyphs:
			reg.horz = self._horz
	
	def populate(self, region_image, bLine=False):
		imLabeled, n = ndimage.label(region_image)
		
		for iLabel in range(n):
			imMask = np.uint8(imLabeled == iLabel+1)*255
			if bLine:
				self.lines.append( LineRegion( imMask, self.text_image ) )
			else:
				self.glyphs.append( GlyphRegion( imMask, self.text_image ) )
	
	
	def organize_components(self, horz = None):
		if horz:
			self._horz = horz
		else: 
			self.vote_on_orientation()
		
		# Map glyphs to lines
		self.clear_line_glyphs()
		for glyph in self.glyphs:
			vOverlap = [ glyph.overlap(l) for l in self.lines ]
			iMatch = np.argmax( vOverlap )
			glyph.line = self.lines[iMatch]
			glyph.horz = self.lines[iMatch].horz
			self.lines[iMatch].glyphs.append( glyph )
		
		self.lines.sort()	
		self.glyphs.sort()
		for line in self.lines:
			 line.glyphs.sort()
		
		# vGlyphsTemp = list()
		for i, line in enumerate(self.lines):
			self.lines[i].glyphs.sort()
			# vGlyphsTemp.extend(line.glyphs)
		# self.glyphs = vGlyphsTemp
		
	
	def vote_on_orientation(self):
		vVotes = [ reg.horz for reg in self.lines if reg.horz is not None ]
		iVotes = np.sum( vVotes )
		iTotal = len( vVotes )
		# vVotes = [ reg.horz for reg in self.glyphs if reg.horz ]
		# iVotes += np.sum( vVotes )
		# iTotal += len( vVotes )
		
		self._horz = True
		if iTotal:
			self._horz = ( iVotes / iTotal ) > 0.5
	
	def clear_line_glyphs(self):
		for line in self.lines:
			line.glyphs.clear()
			
	def get_line_list(self):
		self.lines.sort()
		return self.lines
		
	def get_glyph_list(self):
		self.glyphs.sort()
		return self.glyphs
		
	def get_glyphs_by_line(self, line): 
		line.glyphs.sort()
		return line.glyphs
		
	def shape(self):
		return self.image.shape
	
	def __len__(self):
		return len(self.lines) + len(self.glyphs)

