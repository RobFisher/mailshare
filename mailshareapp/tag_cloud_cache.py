from django.conf import settings
from mailshareapp.models import Mail, Contact, Tag
import tags
import people
import search
import os
import teams

def _get_tag_cloud_html(team_id):
    team_search = search.get_team_search(team_id, 7)
    team_emails = team_search.get_query_set()
    month_search = search.get_team_search(team_id, 30)
    tag_cloud_html = '<div id="tag_cloud" class="tag_cloud">'
    tag_cloud_html += tags.search_results_to_tag_cloud_html(team_emails, month_search)
    tag_cloud_html += '</div>'

    # it's untidy to put top senders code in the tag cloud cache like this, but it gets us
    # going for now.
    # TODO - tidy this up; possibly just search and replace "tag_cloud" with "index_page_stats" in this file.
    tag_cloud_html += '<p>Top senders in the last week:</p>'
    tag_cloud_html += people.search_results_to_top_senders_html(team_emails, month_search)

    return tag_cloud_html


def get_filename(team_id, temp):
    path = settings.MAILSHARE_CACHE_PATH
    filename = 'tag_cloud_cache_' + str(team_id)
    if temp:
        filename += '_tmp'
    return path + '/' + filename


def save_tag_cloud(team_id, html):
    temp_filename = get_filename(team_id, True)
    temp_file = open(temp_filename, 'w')
    temp_file.write(html)
    temp_file.close()

    # we want to atomically replace the contents of the file, we can
    # do this with a rename on Linux:
    # http://stackoverflow.com/questions/2333872/atomic-writing-to-file-with-python

    real_filename = get_filename(team_id, False)
    os.rename(temp_filename, real_filename)


def update_cached_tag_cloud(team_id):
    html = _get_tag_cloud_html(team_id)
    try:
        save_tag_cloud(team_id, html)
    except IOError:
        pass
    return html


def update_cached_tag_clouds_by_contacts(contacts, verbose=False):
    """Update all the caches affected by the specified set of contacts."""
    at_least_one_team_updated = False
    for contact in contacts:
        if contact.id in teams.teams_by_contact_id:
            if verbose:
                print "Updating tag cloud cache for team " + teams.teams_by_contact_id[contact.id].name
            update_cached_tag_cloud(contact.id)
            at_least_one_team_updated = True

    if at_least_one_team_updated:
        if verbose:
            print "Updating tag cloud for all teams"
        update_cached_tag_cloud(0)
        if verbose:
            print "Done."


def get_cached_tag_cloud(team_id):
    filename = get_filename(team_id, False)
    html = ''

    try:
        cache_file = open(filename, 'r')
    except IOError:
        html = update_cached_tag_cloud(team_id)
    else:
        html = cache_file.read()

    return html
