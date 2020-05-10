from django.urls import path

from . import views

app_name = 'sobti'
urlpatterns = [
	path('', views.TextList, name='texts'),
	path('<int:text_id>/', views.ManuscriptList, name='manuscripts'),
	# path('<int:text_id>/add_manuscript', views.AddManuscript, name='add_manuscript'),
	path('<int:text_id>/<int:manuscript_id>/', views.PageList, name='pages'),
	path('<int:text_id>/<int:manuscript_id>/<int:page_id>/', views.PageDetail, name='page_detail'),
	path('<int:text_id>/<int:manuscript_id>/<int:page_id>/ipt', views.ImageProcessing, name='image_processing_tests'),
	path('<int:text_id>/<int:manuscript_id>/<int:page_id>/process', views.PageProcess, name='page_process'),
	path('<int:text_id>/<int:manuscript_id>/<int:page_id>/modify_glyph', views.ModifyGlyphData, name='modify_glyph_data'),
	path('<int:text_id>/<int:manuscript_id>/<int:page_id>/move_glyph', views.MoveGlyphPosition, name='move_glyph_position'),
	path('get/ajax/validate/nickname', views.checkNickName, name = 'validate_nickname'),
	path('get/ajax/validate/polygon', views.GetPolygon, name = 'get_polygon'),
]
