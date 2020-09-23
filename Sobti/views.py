from django.shortcuts import render, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from django.db.models import Max

from .models import *
from .forms import *

from .LineGlyph import *
from .LineGlyphFunctions import *

import os, shutil

################################################################################
# STANDARD PAGE VIEWS
################################################################################
def TextList(request):
	if request.method == 'POST':
		form = NewTextForm(request.POST)
		form.save()			
		return HttpResponseRedirect(reverse('sobti:texts'))

	else:
		form = NewTextForm()
		context = { 'text_list': Text.objects.order_by('title'),
					'form': form,
					'error_message': "ⲙⲡⲟⲩϫⲓⲙⲓ ⲙⲡⲓϫⲟⲙ"}
		return render(request, 'Sobti/text_list.html', context)

def ManuscriptList(request, text_id):
	text = get_object_or_404(Text, pk=text_id)
	if request.method == 'POST':
		form = NewManuscriptForm(request.POST)
		m = form.save(commit=False)
		m.text = text
		form.save()
		return HttpResponseRedirect(reverse('sobti:manuscripts', args=(text_id,)))

	else:
		form = NewManuscriptForm()
		context = { 'text': text,
					'form': form,
					'error_message': "ⲙⲡⲟⲩϫⲓⲙⲓ ⲙⲡⲓϫⲟⲙ"}
					
		if request.is_ajax() and request.method == "GET":
			return render(request, 'Sobti/manuscripts_sub.html', context)
		
		return render(request, 'Sobti/manuscripts.html', context)



def PageList(request, text_id, manuscript_id):
	manuscript = get_object_or_404(Manuscript, pk=manuscript_id)
	
	# && BEGIN DEBUG OUTPUT &&
	print('')
	print('BEGIN: DEBUGGING MISMATCHED TEXT/MS')
	print('Text ID (passed to fn as arg): %i' % text_id)
	print('Text ID (taken via ms id):     %i' % manuscript.text.id)
	print('END: DEBUGGING MISMATCHED TEXT/MS')
	print('')
	# && END DEBUG OUTPUT &&
	
	
	
	if request.method == 'POST':
		form = NewPageForm(request.POST, request.FILES)
		page = form.save(commit=False)
		page.manuscript = manuscript
		form.save()
		
		sError = PageProcess(page)
		if sError is None:
			return HttpResponseRedirect(reverse('sobti:pages', args=(text_id,manuscript_id,)))
		else:
			return HttpResponse(sError)

	else:
		form = NewPageForm()
		
		# Set the initial value in the form to the next available page number
		if manuscript.page_set.count() > 0:
			iMax = manuscript.page_set.aggregate(Max('number_in_manuscript'))['number_in_manuscript__max']
			form.SetDefaultNewPageNumber(iMax+1)
		
		context = { 'manuscript': manuscript,
					'form': form,
					'error_message': "ⲙⲡⲟⲩϫⲓⲙⲓ ⲙⲡⲓϫⲟⲙ"}
		return render(request, 'Sobti/pages.html', context)

	
def PageDelete(request, text_id, manuscript_id, page_id):
	
	page = get_object_or_404(Page, pk=page_id)
	vPages = [page]
	
	# m = get_object_or_404(Manuscript, pk=manuscript_id)
	# vPages = m.page_set.all()
	for page in vPages:
		
		time_zero = time.time()
		
		if os.path.isdir(GetPageDataPath(page,True)):
			shutil.rmtree(GetPageDataPath(page,True))
			
		print('Deleting files: Time elapsed: %f' % (time.time()-time_zero))
		time_zero = time.time()
		
		page.delete()
		
		print('Deleting db stuff: Time elapsed: %f' % (time.time()-time_zero))
		time_zero = time.time()
		
		
		# && BEGIN DEBUG OUTPUT &&
		print('\x1b[0;31;40m' + ('🗙'*80))
		print('PAGE DELETED FROM: ' 
			+ page.manuscript.text.title 
			+ ' — ' + page.manuscript.accession_number 
			+ (', Page %i' % page.number_in_manuscript))
		print(('🗙'*80) + '\x1b[0m')
		# && END DEBUG OUTPUT &&
	
	return HttpResponseRedirect(reverse('sobti:pages', args=(page.manuscript.text.pk,page.manuscript.pk,)))
	

	

import json

def PageDetail(request, text_id, manuscript_id, page_id):
	page = get_object_or_404(Page, pk=page_id)
	iMaxWidth = np.max([g.image.width for g in Glyph.objects.all()])
	lines = page.line_set.order_by('number_in_page')
	
	vdLine = []
	for dbLine in lines:
		
		vdGlyph = []
		for dbGlyph in dbLine.glyph_set.order_by('number_in_line'):
			vdGlyph.append( {   'pk': dbGlyph.pk,
								'number_in_line': dbGlyph.number_in_line,
								'number_in_page': dbGlyph.number_in_page,
								'unicode_glyphs': dbGlyph.unicode_glyphs,
								'polygon': [list(xy) for xy in dbGlyph.shape] } )
		
		vdLine.append( {	'pk': dbLine.pk, 
							'number_in_page': dbLine.number_in_page,
							'number_in_manuscript': dbLine.number_in_manuscript,
							'polygon': [list(xy) for xy in dbLine.shape],
							'glyphs': vdGlyph } )
		
		# break
		
	# Deal with an empty layer set (when the image hasn't been processed properly)
	if page.layer_set.count() <= 0:
		jsDataPackage = [] # Send empty data if it doesn't get filled
	else:
		dFacsimile = {  'width': page.layer_set.filter(number=1).get().image.width,
						'height': page.layer_set.filter(number=1).get().image.height,
						'url': page.layer_set.filter(number=1).get().image.url }
		
		# Dump everything into a JSON and hand it to the front end
		jsDataPackage = json.dumps({'lines': vdLine, 'facsimile': dFacsimile})
									 
	sTemplateFilename = 'Sobti/sign_list_element.html'
	context = { 'page': page,
				'data_package': jsDataPackage,
				'glyph_max_width': iMaxWidth,
				'error_message': "ⲙⲡⲟⲩϫⲓⲙⲓ ⲙⲡⲓϫⲟⲙ",
				'template_filename': sTemplateFilename }
	
	return render(request, sTemplateFilename, context)

from django.db.models import Q
# Q(alias__exact='')

def SignList(request):
	vGlyphs = Glyph.objects.exclude(Q(unicode_glyphs__exact='')).order_by('unicode_glyphs')
	sTemplateFilename = 'Sobti/signlist.html'
	context = {'glyphs': vGlyphs}
	return render(request, sTemplateFilename, context) 

def ImageProcessing(request, text_id, manuscript_id, page_id):
	page = get_object_or_404(Page, pk=page_id)
	glyph = page.line_set.all()[0].glyph_set.all()[0]
	glyph = Glyph.objects.all()[0]
	# vPoly = page.line_set.all()[0]
	# vPoly = vPoly.polygon_set.all()[0].polygonpoint_set.all()
	iMaxWidth = np.max([g.image.width for g in Glyph.objects.all()])
	sTemplateFilename = 'Sobti/image_processing_tests.html'
	context = { 'glyph': glyph,
				'glyph_max_width': iMaxWidth,
				'error_message': "ⲙⲡⲟⲩϫⲓⲙⲓ ⲙⲡⲓϫⲟⲙ",
				'template_filename': sTemplateFilename}
	return render(request, sTemplateFilename, context)
	


################################################################################
# MORE ADVANCED PROCESSING OF INPUT DATA
################################################################################


from django.http import JsonResponse

def ModifyGlyphData(request, text_id, manuscript_id, page_id):
	
	if request.is_ajax() and request.method == 'POST':
		
		vReq = json.loads(request.body)
		
		iPk = vReq['pk']
		sField = vReq['field']
		sValue = vReq['value']
		
		g = Glyph.objects.get(pk=iPk)
		setattr(g, sField, sValue)
		g.save()
		
		return JsonResponse({   'success': True, 
								'postpk': g.pk,
								'field': sField,
								'value': getattr(g, sField)})
		
	return JsonResponse({'success': False})

def MoveGlyphPosition(request, text_id, manuscript_id, page_id):
	if request.is_ajax() and request.method == 'POST':
		vReq = json.loads(request.body)
		
		for oNewPos in vReq['new_glyph_positions']:
			g = Glyph.objects.get(pk=oNewPos['glyph_pk'])
			g.number_in_line = oNewPos['new_pos_rel']
			g.number_in_page = oNewPos['new_pos_abs']
			g.save()
		
		for oNewLine in vReq['new_glyph_lines']:
			g = Glyph.objects.get(pk=oNewLine['glyph_pk'])
			g.line = g.line.page.line_set.get(number_in_page=oNewLine['new_line_pos'])
			g.save()
				
		return JsonResponse({ 'success': True })
		
	return JsonResponse({'success': False})









