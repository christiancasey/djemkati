from django.db import models
from django.utils import timezone


class Collection(models.Model):
	def __str__(self):
		return self.name
	
	name = models.CharField("Museum or private collection", max_length=500)

class Text(models.Model):
	def __str__(self):
		return self.title
	
	title = models.CharField("Name of text", max_length=200)
	era_composed = models.CharField("Approximate date of the text's original composition", max_length=200, blank=True)

class ManuscriptManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().order_by('accession_number')
		
class Manuscript(models.Model):
	def __str__(self):
		return self.text.title + ' – ' + self.collection.name + ': ' + self.accession_number
	
	text = models.ForeignKey(Text, on_delete=models.CASCADE)
	collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
	accession_number = models.CharField("Accession number", max_length=200, blank=True)
	find_date = models.CharField("Date found in modern era", max_length=300, blank=True)
	provenance = models.CharField("Geographic location of origin", max_length=200, blank=True)
	date_added = models.DateTimeField("Date added to the database", blank=True, default=timezone.now)
	marked_for_deletion = models.BooleanField("Removing a text triggers more operations", default=False)

	objects = ManuscriptManager()

class PageManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().order_by('number_in_manuscript')

class Page(models.Model):
	def __str__(self):
		return self.manuscript.text.title \
		+ ' – ' + self.manuscript.collection.name \
		+ ': ' + self.manuscript.accession_number \
		+ (', p. %i' % self.number_in_manuscript )
	
	manuscript = models.ForeignKey(Manuscript, on_delete=models.CASCADE)
	number_in_manuscript = models.IntegerField('Page number in manuscript')
	image = models.FileField(upload_to='upload/%Y-%m-%d', blank=False)
	image_preview = models.ImageField(blank=True)
	image_thumbnail = models.ImageField(blank=True)
	horizont = models.BooleanField("Text is horizontal (not vertical)", default=True)
	
	objects = PageManager()

class Layer(models.Model):
    page = models.ForeignKey(Page, on_delete=models.CASCADE)
    number = models.IntegerField("Layer number in PSD", default=0)
    image = models.ImageField(blank=True)

class RegionManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().order_by('number_in_page')
		
class Line(models.Model):
	def __str__(self):
		return self.page.manuscript.accession_number + (', p. %i, l. %i' % (self.page.number_in_manuscript, self.number_in_page))

	page = models.ForeignKey(Page, on_delete=models.CASCADE)
	image = models.ImageField(blank=True, null=True)
	number_in_page = models.IntegerField("Sequence of line in page", default=0)
	number_in_manuscript = models.IntegerField("Sequence of line in manuscript as a whole", null=True)
	# image_filename = models.CharField("Name of line image minus extension", max_length=300, blank=True, default='')
	# polygon = models.ForeignKey(Polygon, on_delete=models.CASCADE, null=True, blank=True)
	
	objects = RegionManager()
	
class Glyph(models.Model):
	def __str__(self):
		return self.line.page.manuscript.accession_number + (', p. %i, l. %i, g. %i' % (self.line.page.number_in_manuscript, self.line.number_in_page, self.number_in_line))
		
	line = models.ForeignKey(Line, on_delete=models.CASCADE)
	image = models.ImageField(blank=True)
	number_in_line = models.IntegerField("Sequence of glyph in line", default=0)
	number_in_page = models.IntegerField("Sequence of glyph in page", null=True, blank=True)
	# image_filename = models.CharField("Name of glyph image minus extension", max_length=300, default='')
	unicode_glyphs = models.CharField("Unicode hieroglyphs", max_length=50, blank=True)
	manuel_de_codage = models.CharField("Manuel de Codage hieroglyphs", max_length=100, blank=True)
	moller_number = models.CharField("Entry number in Möller's Palaeographie", max_length=50, blank=True)
	mainz_number = models.CharField("Entry number in Mainz Palaeographie", max_length=100, blank=True)
	# polygon = models.ForeignKey(Polygon, on_delete=models.CASCADE, null=True, blank=True)
	
	# objects = models.Manager()
	objects = RegionManager()
	
class Polygon(models.Model):
    def __str__(self):
        s = '(' + self.polygon_type + ')'
        if self.line:
            s = s + ' ' + self.line.page.manuscript.text.title \
    		+ ' – ' + self.line.page.manuscript.collection.name \
    		+ ': ' + self.line.page.manuscript.accession_number \
    		+ (', p. %i, l. %i' % (self.line.page.number_in_manuscript, self.line.number_in_page) )
            
            if self.glyph:
                s = s + (', g. %i' % self.glyph.number_in_line)
            
        return s
    
    polygon_type = models.CharField("Type of polygon (line or glyph)", max_length=5, blank=True, default="Empty")
    line = models.ForeignKey(Line, on_delete=models.CASCADE, null=True)
    glyph = models.ForeignKey(Glyph, on_delete=models.CASCADE, null=True)
    x_min = models.IntegerField()
    y_min = models.IntegerField()
    x_max = models.IntegerField()
    y_max = models.IntegerField()
    x_cent = models.IntegerField()
    y_cent = models.IntegerField()
	

class PointManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().order_by('t_coordinate')
		
class PolygonPoint(models.Model):
	polygon = models.ForeignKey(Polygon, on_delete=models.CASCADE)
	x_coordinate = models.IntegerField()
	y_coordinate = models.IntegerField() 
	t_coordinate = models.IntegerField("Position in sequence of points")
	
	objects = PointManager()
	
class Source(models.Model):
	oclc = models.CharField("OCLC of source.", max_length=500, blank=True)
	
class BibEntry(models.Model):
	text = models.ForeignKey(Text, on_delete=models.CASCADE)
	source = models.ForeignKey(Source, on_delete=models.CASCADE)
