# License: https://github.com/RobFisher/mailshare/blob/master/LICENSE

import re
import math
from django.utils.html import strip_tags
from django.db.models import Q
import models

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


def tag_to_html(t):
    """Render the specified tag as HTML."""
    result = '<a href="/search/?tag_id='
    result += str(t.id)
    result += '">'
    result += t.name
    result += '</a>'
    return result


def mail_tags_to_html_list(m):
    result = ''
    tags = m.tags.all()
    if len(tags) > 0:
        result += tag_to_html(tags[0])
    for t in tags[1:]:
        result += ', '
        result += tag_to_html(t)
    return result


def mail_tags_to_html(m):
    """Render an emails tags to HTML."""
    result = '<div class="tags"><p>Tags: <span id="taglist_' + str(m.id)  + '">'
    result += mail_tags_to_html_list(m) + '</span>'
    result += '<input class="hidden" id="tagbox_' + str(m.id)
    result += '" onkeypress="tag_key(event, ' + str(m.id)
    result += ')" onblur="tagbox_blur(' + str(m.id) + ')" />'
    result += '<input type="button" class="shown" value="+" id="tagbutton_'
    result += str(m.id) + '" onClick="add_tag(' + str(m.id) + ')" />'
    result += '</p></div>'
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


def search_results_to_tag_cloud_html(queryset):
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
            result += '<span style="font-size: ' + font_size + 'px; padding: ' + padding + 'px;">'
            result += tag_to_html(tag) + ' '
            result += '</span>'
    return result
