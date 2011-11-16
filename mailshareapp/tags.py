# License: https://github.com/RobFisher/mailshare/blob/master/LICENSE

import re
import math
from django.utils.html import strip_tags
from django.db.models import Q
import models
import search

def get_or_create_tag(tag_name):
    """Return tag with the specified name, creating it if it doesn't exist."""
    tag_name = tag_name.strip().lower()
    tags = models.Tag.objects.filter(name=tag_name)
    tag = None
    if len(tags) == 0:
        tag = models.Tag()
        tag.name = tag_name
        tag.auto = False
        tag.save()
    else:
        tag = tags[0]
    return tag


def add_tag_by_name(m, tag_name):
    """Add the named tag to the specified email."""
    m.tags.add(get_or_create_tag(tag_name))


def add_autotags_to_mail(m):
    """Search the mail for each autotag and add it if found"""
    tags = models.Tag.objects.filter(auto=True)
    mail_as_queryset = models.Mail.objects.filter(id=m.id)
    for t in tags:
        matches = mail_as_queryset.filter(
            Q(subject__search=t.name) |
            Q(body__search=t.name))
        if len(matches) > 0:
            m.tags.add(t)


user_tags_expression = r'tags:\s*([,-\.\w ]*)'
user_tags_compiled = re.compile(user_tags_expression, re.IGNORECASE)

def add_usertags_to_mail(m):
    body = m.body
    # strip html tags from HTML emails before parsing out Mailshare tags
    if m.content_type.find('html') != -1:
        body = strip_tags(m.body)
    taglists = re.findall(user_tags_compiled, body)
    for taglist in taglists:
        tags = taglist.split(',')
        for tag in tags:
            if len(tag) <= models.Tag.MAX_TAG_NAME_LENGTH:
                add_tag_by_name(m, tag)


def add_tags_to_mail(m):
    """Add tags to a mailshareapp.models.Mail object. This includes tags that appear in
    the email subject or body that have their auto attribute set, and tags added by
    the user by typing "tags:" in an email."""
    add_autotags_to_mail(m)
    add_usertags_to_mail(m)


def apply_autotag(tag):
    """For a new tag, find all the emails that contain it and add it to them."""
    if not tag.auto:
        return
    mails_with_tag = models.Mail.objects.filter(
        Q(subject__search=tag.name) |
        Q(body__search=tag.name))
    for m in mails_with_tag:
        m.tags.add(tag)


def tag_to_html(t, s=None):
    """Render the specified tag as HTML."""
    tag_search = search.get_tag_id_search(t.id)
    if s:
        tag_search = s.add_and(tag_search)
    result = '<a href="' + tag_search.get_url_path()
    result += '">'
    result += t.name
    result += '</a>'
    return result


def tag_to_delete_html(mail_id, t):
    """Render a delete link for the specified mail and tag as HTML."""
    result = '[<a href="#" title="Delete tag" onclick="delete_tag(' + str(mail_id) + ',' + str(t.id) + '); return false;">x</a>]'
    return result


def undo_delete_html(mail_id, t):
    """Render an undo link for a deleted tag as HTML."""
    result = ' Tag ' + t.name + ' deleted ['
    result += '<a href="#" onclick="add_tag_to_email(' + str(mail_id) + ',\'' + t.name + '\'); return false;">'
    result += 'undo</a>]'
    return result


def mail_tags_to_html_list(m, search_object):
    result = ''
    tags = m.tags.all()
    if len(tags) > 0:
        result += tag_to_html(tags[0], search_object)
        result += tag_to_delete_html(m.id, tags[0])
    for t in tags[1:]:
        result += ', '
        result += tag_to_html(t, search_object)
        result += tag_to_delete_html(m.id, t)
    return result


def add_tag_button_html(mail_id):
    result = '<input class="hidden" id="tagbox_' + str(mail_id)
    result += '" onkeypress="tag_key(event, ' + str(mail_id)
    result += ')" onblur="tagbox_blur(' + str(mail_id) + ')" />'
    result += '<input type="button" class="shown" value="+" id="tagbutton_'
    result += str(mail_id) + '" onClick="add_tag(' + str(mail_id) + ')" />'
    return result


def mail_tags_bar_html(m, search_object):
    """Generate tags bar for mail in HTML."""
    result = '<div class="tags"><p>Tags: <span id="taglist_' + str(m.id)  + '">'
    result += mail_tags_to_html_list(m, search_object) + '</span>'
    result += add_tag_button_html(m.id)
    result += '</p></div>'
    return result


def mail_tags_multibar_html(search_object, mail_ids, tags_only=False):
    if len(mail_ids) == 0:
        return ''
    result = ''
    if not tags_only:
        result += '<span id="multi_bar_tag_list">'
    all_tags = set([])
    common_tags = set([])
    first_mail = True
    for mail_id in mail_ids:
        try:
            m = models.Mail.objects.get(id=mail_id)
        except:
            pass
        else:
            mail_tags = set(m.tags.all())
            all_tags = all_tags | mail_tags
            if first_mail:
                common_tags = mail_tags
                first_mail = False
            else:
                common_tags = common_tags & mail_tags

    tags_list = sorted(all_tags, key=lambda t: t.name)
    tags_html_list = []
    for tag in tags_list:
        tag_html = ''
        common_tag = (tag in common_tags)
        if not common_tag:
            tag_html += '<span class="not_common_tag">'
        tag_html += tag_to_html(tag, search_object)
        tag_html += tag_to_delete_html(-1, tag)
        if not common_tag:
            tag_html += '[<a href="#" title="Add tag to all selected emails" onclick="add_tag_to_email(-1, \'' + tag.name + '\'); return false;">+</a>]</span>'
        tags_html_list.append(tag_html)
    result += ', '.join(tags_html_list)

    if not tags_only:
        result += "</span>"
        result += add_tag_button_html(-1)
    return result


def build_tags_histogram(queryset):
    """Given a queryset containing Mail objects, return a sorted list of (tag, frequency) tuples."""
    tags_dict = {}
    for mail in queryset:
        tags = mail.tags.all()
        for tag in tags:
            if tag in tags_dict:
                tags_dict[tag] += 1
            else:
                tags_dict[tag] = 1
    tags_list = tags_dict.items()
    tags_histogram = sorted(tags_list, key=lambda entry: entry[0].name)
    return tags_histogram


def search_results_to_tag_list_html(queryset):
    """Given a queryset containing Mail objects, return a tag list rendered in HTML"""
    result = '<ul>'
    h = build_tags_histogram(queryset)
    for (tag, frequency) in h:
        result += '<li>' + tag_to_html(tag) + ': ' + str(frequency) + '</li>'
    result += '</ul>'
    return result


MIN_FONT_SIZE = 8
MAX_FONT_SIZE = 24

def get_tag_cloud_size(freq, max_freq, min_freq):
    """Return font size given the frequency of a tag and the min and max frequencies found in the set of tags."""
    min_freq = min_freq - 0.5
    max_freq = max_freq + 0.5
    freq -= min_freq
    max_freq -= min_freq
    proportion = math.sqrt(freq) / math.sqrt(max_freq)
    font_size = ((MAX_FONT_SIZE-MIN_FONT_SIZE) * proportion) + MIN_FONT_SIZE
    return int(font_size)


def search_results_to_tag_cloud_html(queryset, search=None):
    """Given a queryset containing Mail objects, return a tag cloud rendered in HTML"""
    result = ''
    h = build_tags_histogram(queryset)
    if len(h) > 0:
        min_freq = min(h, key=lambda entry: entry[1])[1]
        max_freq = max(h, key=lambda entry: entry[1])[1]
        for (tag, frequency) in h:
            size = get_tag_cloud_size(frequency, max_freq, min_freq)
            font_size = str(size)
            padding = str(size/4)
            result += '<span style="font-size: ' + font_size + 'px; padding: ' + padding + 'px;"'
            result += ' title="' + str(frequency) + ' occurrence'
            if frequency != 1:
                result += 's'
            result += '">' + tag_to_html(tag, search) + ' '
            result += '</span>'
    return result
