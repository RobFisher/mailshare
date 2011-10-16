# License: https://github.com/RobFisher/mailshare/blob/master/LICENSE

import re
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
    """Search the mail body for each autotag and add it if found"""
    # TODO - maybe it would be quicker or better to make a queryset out of the
    # email and use a common function for adding tags to new emails and new
    # tags to existing emails
    tags = models.Tag.objects.filter(auto=True)
    for t in tags:
        tag_lowercase = t.name.lower()
        if m.subject.lower().find(tag_lowercase) != -1:
            m.tags.add(t)
        # TODO: find out why this gives UnicodeDecodeError: 'ascii' codec can't decode
        # Where is the ascii here?
        #elif m.body.lower().find(tag_lowercase) != -1:
        else:
            try:
                found = m.body.lower().find(tag_lowercase)
            except UnicodeDecodeError:
                pass
            else:
                if found != -1:
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
        Q(subject__icontains=tag.name) |
        Q(body__icontains=tag.name))
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
    result = '<div class="tags"><p>Tags: <span id="taglist_' + str(m.id)  + '"'
    result += mail_tags_to_html_list(m) + '</span>'
    result += '<input class="hidden" id="tagbox_' + str(m.id)
    result += '" onkeypress="tag_key(event, ' + str(m.id)
    result += ')" onblur="tagbox_blur(' + str(m.id) + ')" />'
    result += '<input type="button" class="shown" value="+" id="tagbutton_'
    result += str(m.id) + '" onClick="add_tag(' + str(m.id) + ')" />'
    result += '</p></div>'
    return result
