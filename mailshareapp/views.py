# License: https://github.com/RobFisher/mailshare/blob/master/LICENSE

from django.template import RequestContext, loader
from django.http import HttpResponse
from django.db.models import Q
from mailshareapp.models import Mail, Contact
import email_utils

def index(request):
    t = loader.get_template('index.html')
    c = RequestContext(request)
    return HttpResponse(t.render(c))


def get_string(request, parameter):
    """Returns a string from a GET request if available, otherwise returns ''"""
    result = ''
    if parameter in request.GET:
        result = request.GET[parameter]
    return result


def get_int(request, parameter):
    """Returns an int from a GET request if available, otherwise returns -1"""
    result = -1
    if parameter in request.GET:
        try:
            result = int(request.GET[parameter])
        except ValueError:
            pass
    return result


def search(request):
    search_query = get_string(request, 'query')
    sender_id = get_int(request, 'sender')
    sender_html = ''
    results = Mail.objects.all()
    if search_query != '':
        results = results.filter(
            Q(subject__icontains=search_query) |
            Q(body__icontains=search_query))
    if sender_id != -1:
        results = results.filter(sender__id=sender_id)
        try:
            sender = Contact.objects.get(id=sender_id)
        except Contact.DoesNotExist:
            pass
        else:
            sender_html = email_utils.contact_to_html(sender)
    t = loader.get_template('search.html')
    c = RequestContext(request, {
        'search_query': search_query,
        'sender_html': sender_html,
        'results' : results,
    })
    return HttpResponse(t.render(c))
