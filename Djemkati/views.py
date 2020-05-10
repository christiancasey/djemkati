from django.http import HttpResponse

def index(request):
	return HttpResponse('<h1><a href="/Sobti/">Texts</a></h1>')

