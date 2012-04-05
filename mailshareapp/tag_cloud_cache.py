from django.conf import settings
from mailshareapp.models import Mail, Contact, Tag
import tags
import search
import os

def _get_tag_cloud_html(team_id):
    team_search = search.get_team_search(team_id, 7)
    team_emails = team_search.get_query_set()
    month_search = search.get_team_search(team_id, 30)
    tag_cloud_html = tags.search_results_to_tag_cloud_html(team_emails, month_search)
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
