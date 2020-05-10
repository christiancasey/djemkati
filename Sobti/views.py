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
        if form.is_valid():
            title = form.cleaned_data['title']
            era_composed = form.cleaned_data['era_composed']
            
            t = Text(title=title, era_composed=era_composed)
            t.save()
            
            return HttpResponseRedirect(reverse('sobti:texts'))

    else:
        form = NewTextForm()
            
        sTemplateFilename = 'Sobti/text_list.html'
        context = { 'text_list': Text.objects.order_by('title'),
                    'form': form,
                    'error_message': "ⲙⲡⲟⲩϫⲓⲙⲓ ⲙⲡⲓϫⲟⲙ",
                    'template_filename': sTemplateFilename}
        return render(request, 'Sobti/text_list.html', context)

def ManuscriptList(request, text_id):
    text = get_object_or_404(Text, pk=text_id)
    sTemplateFilename = 'Sobti/manuscripts_in_text.html'
    context = { 'text': text,
                'error_message': "ⲙⲡⲟⲩϫⲓⲙⲓ ⲙⲡⲓϫⲟⲙ",
                'template_filename': sTemplateFilename}
    return render(request, sTemplateFilename, context)

def PageList(request, text_id, manuscript_id):
    manuscript = get_object_or_404(Manuscript, pk=manuscript_id)
    sTemplateFilename = 'Sobti/pages_in_manuscript.html'
    context = { 'text': manuscript.text,
                'manuscript': manuscript,
                'error_message': "ⲙⲡⲟⲩϫⲓⲙⲓ ⲙⲡⲓϫⲟⲙ",
                'template_filename': sTemplateFilename}
    return render(request, sTemplateFilename, context)


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
# ADD ELEMENTS TO DATABASE
################################################################################
def AddManuscript(request, text_id):
    # text = get_object_or_404(Text, pk=text_id)
    # return render(request, 'Sobti/add_manuscript.html', {'text': text, 
    #                                                     'error_message': "ⲙⲡⲟⲩϫⲓⲙⲓ ⲙⲡⲓϫⲟⲙ"})
    # Handle file upload
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            newman = Manuscript(image = request.FILES['docfile'])
            newman.save()

            # Redirect to the document list after POST
            return HttpResponse('<h1>done</h1>') #Redirect(reverse('Ptoubo.Sobti.views.TextList'))
    else:
        form = DocumentForm() # A empty, unbound form

    # Load text for the list page
    texts = Text.objects.all()

    # # Render list page with the documents and the form
    # return render_to_response(
    #     'Sobti/text_list.html',
    #     {'texts': texts, 'form': form},
    #     context_instance=RequestContext(request)
    # )
    text = get_object_or_404(Text, pk=text_id)
    return render(request, 'Sobti/add_manuscript.html', {   'text': text, 
                                                            'error_message': "ⲙⲡⲟⲩϫⲓⲙⲓ ⲙⲡⲓϫⲟⲙ"})

################################################################################
# MORE ADVANCED PROCESSING OF INPUT DATA
################################################################################
from django.conf import settings

def PageProcess(request, text_id, manuscript_id, page_id):
    page = get_object_or_404(Page, pk=page_id)
    
    #### TEMP 
    import Sobti.models as m
    for o in m.Line.objects.all():
        o.delete()
    for o in m.Layer.objects.all():
        o.delete()
    
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
    
    sTemplateFilename = 'Sobti/page_detail.html'
    # sTemplateFilename = 'Sobti/glyph_labeler.html'
    
    return render(request, sTemplateFilename, { 'page': page,
                                                'media_root': settings.MEDIA_ROOT,  
                                                'error_message': "ⲙⲡⲟⲩϫⲓⲙⲓ ⲙⲡⲓϫⲟⲙ"})




from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def ModifyGlyphData(request, text_id, manuscript_id, page_id):
    
    if request.is_ajax and request.method == 'POST':
        
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

@csrf_exempt
def MoveGlyphPosition(request, text_id, manuscript_id, page_id):
    
    
    if request.is_ajax and request.method == 'POST':
        
        vReq = json.loads(request.body)
        
        for oNewPos in vReq['new_glyph_positions']:
            g = Glyph.objects.get(pk=oNewPos['glyph_pk'])
            g.number_in_line = oNewPos['new_pos_rel']
            g.number_in_page = oNewPos['new_pos_abs']
            g.save()
        
        for oNewLine in vReq['new_glyph_lines']:
            g = Glyph.objects.get(pk=oNewLine['glyph_pk'])
            l1 = g.line.page.line_set.get(number_in_page=oNewLine['new_line_pos'])
            l2 = Line.objects.get(pk=oNewLine['new_line_pk'])
            
            print(l1.pk == l2.pk)
            g.line = l1
            # Glyph.objects.get(pk=oNewLine['glyph_pk']).update(line=l1)
            g.save()
        
        
        # print(vNewPos)
        # iPk = vReq['pk']
        # bUp = vReq['up']
        
        # g = Glyph.objects.get(pk=iPk)
        
                
        return JsonResponse({   'success': True, 
                                'postpk': 1 })
        
    return JsonResponse({'success': False})


def GetPolygon(request):

    vPolygon = []
    if request.is_ajax and request.method == "GET":
        if request.GET.get('type', None) == 'line':
            iPk = request.GET.get('pk', None)
            o = Line.objects.filter(pk=iPk)
        
        elif request.GET.get('type', None) == 'glyph':
            iPk = request.GET.get('pk', None)
            o = Glyph.objects.filter(pk=iPk)
        
        if not o is None:
            v = o[0].polygon_set.all()[0].polygonpoint_set.order_by('t_coordinate')
            if len(v) > 0:
                for point in v:
                    vPolygon = vPolygon + [[point.x_coordinate, point.y_coordinate ]]
    
    return JsonResponse({'polygon': vPolygon}, status = 200)
    
def checkNickName(request):
    
    print('cNN()')
    # request should be ajax and method should be GET.
    if request.is_ajax and request.method == "GET":
        # get the nick name from the client side.
        nick_name = request.GET.get("nick_name", None)
        
        print(nick_name)
        print(Line.objects.filter(pk=nick_name))
        # check for the nick name in the database.
        if Line.objects.filter(pk=nick_name).exists():
            # if nick_name found return not valid new friend
            return JsonResponse({"valid":False}, status = 200)
        else:
            # if nick_name not found, then user can create a new friend.
            return JsonResponse({"valid":True}, status = 200)

    return JsonResponse({}, status = 400)








