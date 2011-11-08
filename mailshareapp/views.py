# License: https://github.com/RobFisher/mailshare/blob/master/LICENSE

import datetime
from django.template import RequestContext, loader
from django.http import HttpResponse
from django.db.models import Q
from mailshareapp.models import Mail, Contact, Tag
from mailshareapp.search import Search
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


def get_expanded_html(mail, search=None):
    """Return the HTML representing the expanded email."""
    expanded_html = email_utils.mail_contacts_bar_html(mail, search)
    expanded_html += tags.mail_tags_bar_html(mail, search)
    expanded_html += email_utils.mail_body_html(mail)
    return expanded_html


def search(request):
    search_query = get_string(request, 'query')
    tag_cloud = ''
    expanded_html = ''
    
    search = Search(request.GET.items())

    if len(search.get_query_set()) == 1:
        expanded_html = get_expanded_html(search.get_query_set()[0], search)
    elif len(search.get_query_set()) != 0:
        tag_cloud = tags.search_results_to_tag_cloud_html(search.get_query_set(), search)

    t = loader.get_template('search.html')
    c = RequestContext(request, {
        'query_name': search.get_form_query_name(),
        'hidden_form': search.get_hidden_form_html(),
        'search_html': search.get_html(),
        'tag_cloud': tag_cloud,
        'expanded_html': expanded_html,
        'results' : search.get_query_set(),
    })
    return HttpResponse(t.render(c))
