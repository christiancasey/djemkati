from django.contrib import admin

from .models import *

admin.site.register(Collection)
admin.site.register(Text)
admin.site.register(Manuscript)
admin.site.register(Page)
admin.site.register(Layer)
admin.site.register(Line)
admin.site.register(Glyph)
admin.site.register(Polygon)
admin.site.register(PolygonPoint)
admin.site.register(Source)
admin.site.register(BibEntry)
