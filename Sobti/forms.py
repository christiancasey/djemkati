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
    # number_in_manuscript = forms.CharField(label='Page number in manuscript', max_length=2)
    # image = forms.FileField(label = 'Select the annotated PSD image')
    class Meta:
        model = Page
        fields = ['number_in_manuscript', 'image']







