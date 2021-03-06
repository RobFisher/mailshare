# License: https://github.com/RobFisher/mailshare/blob/master/LICENSE

import datetime
from django.template import RequestContext, loader
from django.http import HttpResponse
from django.db.models import Q
from mailshareapp.models import Mail, Contact, Tag

import email_utils
import tags
import people
import settings
import teams
import search



def index_view(request):
    month_search = search.get_days_search(30)
    t = loader.get_template('index.html')
    default_team_id = 0
    if request.COOKIES.has_key('team'):
        default_team_id = int(request.COOKIES['team'])
    c = RequestContext(request, {
            'teams': teams.teams,
            'selected_team_id':default_team_id,
            'hidden_form': month_search.get_hidden_form_html(),
            'footnote' : settings.MAILSHARE_FOOTNOTE,
    })
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


def get_expanded_html(mail, current_search=None):
    """Return the HTML representing the expanded email."""
    expanded_html = email_utils.mail_contacts_bar_html(mail, current_search)
    expanded_html += tags.mail_tags_bar_html(mail, current_search)
    expanded_html += email_utils.mail_body_html(mail)
    return expanded_html


def search_view(request):
    search_query = get_string(request, 'query')
    tag_cloud = ''
    top_senders = ''
    expanded_html = ''
    
    s = search.Search(request.GET.items())
   
    if len(s.get_query_set()) == 1:
        expanded_html = get_expanded_html(s.get_query_set()[0], s)
    elif len(s.get_query_set()) != 0:
        tag_cloud = tags.search_results_to_tag_cloud_html(s.get_query_set(), s)
        top_senders = people.search_results_to_top_senders_html(s.get_query_set(), s)
    strRequestURL =  "http://"+ request.META['HTTP_HOST']+s.get_rss_url()
    
    t = loader.get_template('search.html')
    c = RequestContext(request, {
        'query_name': s.get_form_query_name(),
        'hidden_form': s.get_hidden_form_html(),
        'search_html': s.get_html(),
        'tag_cloud': tag_cloud,
        'top_senders' : top_senders,
        'expanded_html': expanded_html,
        'results' : s.get_query_set(),
        'rssFeedURL' : strRequestURL,
    })
    response = HttpResponse(t.render(c))
    if request.GET.has_key('recipient-2'):
        response.set_cookie('team', request.GET['recipient-2'])
    return response


def advanced_view(request):
    t = loader.get_template('advanced.html')
    c = RequestContext(request, {'teams': teams.teams})
    response = HttpResponse(t.render(c))
    return response


def teams_view(request):
    t = loader.get_template('teams.html')
    c = RequestContext(request, {'teams': teams.teams})
    response = HttpResponse(t.render(c))
    return response
