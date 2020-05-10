





import Sobti.models as m

from django.db.models import Avg, Max, Min
m.Glyph.objects.aggregate(Max('image.width'))

[g.image.width for g in m.Glyph.objects.all()]
np.max([g.image.width for g in m.Glyph.objects.all()])




p = m.Page.objects.all()[0]

l = p.line_set.create(number_in_page=1)
l = p.line_set.create(number_in_page=2)
l = p.line_set.create(number_in_page=10)
l = p.line_set.create(number_in_page=345)

l = m.Line.objects.all()


p = m.Page.objects.get(pk=1)
l = p.line_set.all()

l = m.Line.objects.all()
for i in l:
  i.delete()
  i.save()

  
p = m.Page.objects.get(pk=1)
for l in p.line_set.order_by('number_in_page'):
  # for g in l.glyph_set.order_by('number_in_line'):
  #   g.delete()
  l.delete()
p.save()

def ClearAll():
for o in m.Layer.objects.all():
    o.delete()

for o in m.Line.objects.all():
    o.delete()




for o in m.Glyph.objects.all():
    o.delete()

for o in m.PolygonPoint.objects.all():
    o.delete()

for o in m.Polygon.objects.all():
    o.delete()


p.line_set.order_by('number_in_page')

for i in range(10):
  p.line_set.create(number_in_page=i+1)
  
  

v = m.Polygon(polygon_type='test')
v.save()
v.polygonpoint_set.create(x_coordinate=0,y_coordinate=0,t_coordinate=0)







v = g.polygon_set.all()
if len(v) > 0:
    v = v[0]

v = l.polygon_set.filter(polygon_type='lined')
if len(v) > 0:
    v = v[0]








  