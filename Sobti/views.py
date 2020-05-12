from django.shortcuts import render, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views import generic

from .models import *
from .forms import *

from .LineGlyph import *
from .LineGlyphFunctions import *


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
    if request.method == 'POST':
        form = NewPageForm(request.POST, request.FILES)
        p = form.save(commit=False)
        p.manuscript = manuscript
        form.save()
        
        PageProcess(p.pk)
        return HttpResponseRedirect(reverse('sobti:pages', args=(text_id,manuscript_id,)))

    else:
        form = NewPageForm()
        context = { 'manuscript': manuscript,
                    'form': form,
                    'error_message': "ⲙⲡⲟⲩϫⲓⲙⲓ ⲙⲡⲓϫⲟⲙ"}
        return render(request, 'Sobti/pages.html', context)

def PageDelete(request, text_id, manuscript_id, page_id):
    page = get_object_or_404(Page, pk=page_id)
    page.delete()
    print('delete page')
    return HttpResponseRedirect(reverse('sobti:pages', args=(page.manuscript.text.pk,page.manuscript.pk,)))
    

from django.conf import settings
def PageProcess(page_id):
    page = get_object_or_404(Page, pk=page_id)
    
    # First change location and filename from upload values to more informative directory tree
    sOldName = page.image.name
    sNewPath = os.path.join(page.manuscript.text.title, 
        page.manuscript.accession_number, 
        '{0:04d}'.format(page.id))
    sNewName = os.path.join(sNewPath, 'page.psd')
    
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
    
    if page.image_preview is None \
        or not page.image_preview.name == ImagePreviewName(page.image.name):
        
        page.image_preview = ImagePreview(page.image)
        page.save()
    
    if page.image_thumbnail is None \
        or not page.image_thumbnail.name == ImageThumbnailName(page.image.name):

        page.image_thumbnail = ImageThumbnail(page.image)
        page.save()
    
    # Delete all of the old images
    vDir = ['glyphs', 'lines', 'layers']
    for sDir in vDir:
        sDirPath = os.path.join(settings.BASE_DIR, settings.MEDIA_ROOT, sNewPath, sDir)
        if os.path.exists(sDirPath):
            RemoveDirectoryContents(sDirPath)
            os.rmdir(sDirPath)
    
    # RemoveDirectoryContents(os.path.join(settings.BASE_DIR, settings.MEDIA_ROOT, sNewPath, 'layers'))
    # RemoveDirectoryContents(os.path.join(settings.BASE_DIR, settings.MEDIA_ROOT, sNewPath, 'lines'))
    
    ExtractLayers(page)
    AnalyzeManuscript(page)
    
    # sTemplateFilename = 'Sobti/page_detail.html'
    # # sTemplateFilename = 'Sobti/glyph_labeler.html'
    # 
    # form = NewPageForm()
    # context = { 'manuscript': page.manuscript,
    #             'form': form,
    #             'error_message': "ⲙⲡⲟⲩϫⲓⲙⲓ ⲙⲡⲓϫⲟⲙ"}
    # return render(request, 'Sobti/pages.html', context)



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
                                'polygon': GetObjectPolygon(dbGlyph,'glyph') } )
        
        vdLine.append( {    'pk': dbLine.pk, 
                            'number_in_page': dbLine.number_in_page,
                            'number_in_manuscript': dbLine.number_in_manuscript,
                            'polygon': GetObjectPolygon(dbLine,'line'),
                            'glyphs': vdGlyph } )
                    
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
                'template_filename': sTemplateFilename}
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









