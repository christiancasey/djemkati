from django import forms
from django.forms import ModelForm

from .models import *

class NewTextForm(ModelForm):
	class Meta:
		model = Text
		fields = ['title', 'era_composed']
	# title = forms.CharField(label='Title', max_length=300)
	# era_composed = forms.CharField(label='Era of Composition', required=False, max_length=100)
	
class NewManuscriptForm(ModelForm):
	class Meta:
		model = Manuscript
		fields = ['collection', 'accession_number']

class NewPageForm(ModelForm):
	number_in_manuscript = forms.IntegerField(label='Page number in manuscript', initial=1)
	image = forms.FileField(label = 'Select the annotated PSD image')
	
	# Allows initial value to be reset to the next available page number by view
	def SetDefaultNewPageNumber(self,i):
		self.fields['number_in_manuscript'].initial = i
	
	class Meta:
		model = Page
		fields = ['number_in_manuscript', 'image']







