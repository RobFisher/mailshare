# License: https://github.com/RobFisher/mailshare/blob/master/LICENSE

import datetime
from django.template import RequestContext, loader
from django.http import HttpResponse
from django.db.models import Q
from mailshareapp.models import Mail, Contact, Tag
import email_utils
import tags

def index(request):
    last_week_emails = Mail.objects.filter(date__gte=datetime.date.today()-datetime.timedelta(7))
    tag_cloud = tags.search_results_to_tag_cloud_html(last_week_emails)
    t = loader.get_template('index.html')
    c = RequestContext(request, {'tag_cloud':tag_cloud,})
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
    mail_id = get_int(request, 'mail_id')
    search_query = get_string(request, 'query')
    sender_id = get_int(request, 'sender')
    tag_id = get_int(request, 'tag_id')
    sender_html = ''
    tag_html = ''
    results = Mail.objects.all()
    if search_query != '':
        results = results.filter(
            Q(subject__search=search_query) |
            Q(body__search=search_query))
    if mail_id != -1:
        results = results.filter(id=mail_id)
    if sender_id != -1:
        results = results.filter(sender__id=sender_id)
        try:
            sender = Contact.objects.get(id=sender_id)
        except Contact.DoesNotExist:
            pass
        else:
            sender_html = email_utils.contact_to_html(sender)
    if tag_id != -1:
        results = results.filter(tags__id=tag_id)
        try:
            tag = Tag.objects.get(id=tag_id)
        except Tag.DoesNotExist:
            pass
        else:
            tag_html = tags.tag_to_html(tag)

    tag_cloud = tags.search_results_to_tag_cloud_html(results)

    t = loader.get_template('search.html')
    c = RequestContext(request, {
        'search_query': search_query,
        'sender_html': sender_html,
        'tag_html': tag_html,
        'tag_cloud': tag_cloud,
        'results' : results,
    })
    return HttpResponse(t.render(c))
