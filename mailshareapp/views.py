from django.template import RequestContext, loader
from django.http import HttpResponse
from django.db.models import Q
from mailshareapp.models import Mail

def index(request):
    t = loader.get_template('index.html')
    c = RequestContext(request)
    return HttpResponse(t.render(c))


def search(request):
    search_query = request.GET['query']
    results = Mail.objects.filter(
        Q(subject__icontains=search_query) |
        Q(body__icontains=search_query))
    t = loader.get_template('search.html')
    c = Context({
        'search_query': search_query,
        'results' : results,
    })
    return HttpResponse(t.render(c))
