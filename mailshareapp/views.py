from django.template import Context, loader
from django.http import HttpResponse

def index(request):
    t = loader.get_template('index.html')
    c = Context()
    return HttpResponse(t.render(c))


def search(request):
    search_query = request.GET['query']
    t = loader.get_template('search.html')
    c = Context({
        'search_query': search_query,
    })
    return HttpResponse(t.render(c))
