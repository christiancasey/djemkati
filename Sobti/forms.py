from django import forms

class NewTextForm(forms.Form):
    # docfile = forms.FileField(label='Select a file',)
    title = forms.CharField(label='Title', max_length=300)
    era_composed = forms.CharField(label='Era of Composition', required=False, max_length=100)