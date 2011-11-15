import datetime
import logging
from dajax.core import Dajax
from dajaxice.decorators import dajaxice_register
from mailshareapp.models import Mail, Contact, Tag
from email_utils import *
from views import get_expanded_html
import tags
import search

@dajaxice_register
def expand_email(request, email_id, url):
    dajax = Dajax()
    search_object = search.get_search_from_url(url)
    email_body = 'Error retrieving email'
    email = Mail.objects.get(pk=email_id)
    if(email):
        email_body=get_expanded_html(email, search_object)
    dajax.add_data({'email_id':email_id, 'email_body':email_body}, 'set_email_body')
    return dajax.json()


@dajaxice_register
def get_email_tags(request, email_id, url):
    dajax = Dajax()
    search_object = search.get_search_from_url(url)
    try:
        mail = Mail.objects.get(id=email_id)
    except(Mail.DoesNotExist, Mail.MultipleObjectsReturned):
        pass
    else:
        tags_html = tags.mail_tags_to_html_list(mail, search_object)
        dajax.add_data({'email_id':email_id, 'tags_html':tags_html}, 'update_tags')
    return dajax.json()


def update_tag_cloud(dajax, search_object):
    tag_cloud_html = tags.search_results_to_tag_cloud_html(search_object.get_query_set(), search_object)
    dajax.add_data({'tag_cloud_html':tag_cloud_html}, 'update_tag_cloud')


@dajaxice_register
def add_tag(request, email_id, tag, url):
    dajax = Dajax()
    search_object = search.get_search_from_url(url)
    mails = Mail.objects.filter(id=email_id)
    if len(mails) > 0:
        t = tags.get_or_create_tag(tag)
        mails[0].tags.add(t)
    tags_html = tags.mail_tags_to_html_list(mails[0], search_object)
    dajax.add_data({'email_id':email_id, 'tags_html':tags_html}, 'update_tags')
    update_tag_cloud(dajax, search_object)
    return dajax.json()


@dajaxice_register
def delete_tag(request, email_id, tag_id, url):
    dajax = Dajax()
    try:
        mail = Mail.objects.get(id=email_id)
        tag = Tag.objects.get(id=tag_id)
    except (Mail.DoesNotExist, Mail.MultipleObjectsReturned, Tag.DoesNotExist, Tag.MultipleObjectsReturned):
        pass
    else:
        mail.tags.remove(tag)
        search_object = search.get_search_from_url(url)
        tags_html = tags.mail_tags_to_html_list(mail, search_object)
        tags_html += tags.undo_delete_html(mail.id, tag)
        dajax.add_data({'email_id':email_id, 'tags_html':tags_html}, 'update_tags')
        update_tag_cloud(dajax, search_object)
    return dajax.json()


@dajaxice_register
def multi_add_tag(request, selected_mails, tag, url):
    dajax = Dajax()
    search_object = search.get_search_from_url(url)
    t = tags.get_or_create_tag(tag)
    for mail_id in selected_mails:
        try:
            m = Mail.objects.get(id=mail_id)
        except:
            pass
        else:
            m.tags.add(t)
    result = tags.mail_tags_multibar_html(search_object, selected_mails, True)
    dajax.add_data({'tags_html':result, 'tags_only':True, 'tags_changed':True}, 'update_multibar')
    update_tag_cloud(dajax, search_object)
    return dajax.json()


@dajaxice_register
def multi_delete_tag(request, selected_mails, tag_id, url):
    dajax = Dajax()
    search_object = search.get_search_from_url(url)
    try:
        tag = Tag.objects.get(id=tag_id)
    except(Tag.DoesNotExist, Tag.MultipleObjectsReturned):
        tag = None
    else:
        for mail_id in selected_mails:
            try:
                mail = Mail.objects.get(id=mail_id)
            except(Mail.DoesNotExist, Mail.MultipleObjectsReturned):
                pass
            else:
                mail.tags.remove(tag)
    result = tags.mail_tags_multibar_html(search_object, selected_mails, True)
    dajax.add_data({'tags_html':result, 'tags_only':True, 'tags_changed':True}, 'update_multibar')
    update_tag_cloud(dajax, search_object)
    return dajax.json()


@dajaxice_register
def tag_completion(request, text):
    dajax = Dajax()
    tags = None
    if len(text) == 1:
        tags = Tag.objects.filter(name__istartswith=text)
    else:
        tags = Tag.objects.filter(name__icontains=text)
    response = []
    for tag in tags:
        response.append(tag.name)
    dajax.add_data({'tags':response}, 'set_tag_completion')
    return dajax.json()


@dajaxice_register
def delete_email(request, email_id):
    dajax = Dajax()
    logger = logging.getLogger('ajax')
    success = False
    try:
        mail = Mail.objects.get(id=email_id)
        logger.info('delete_email ' + datetime.datetime.utcnow().isoformat() + ' id: ' + str(mail.id) + ' subject: ' + mail.subject)
    except:
        pass
    else:
        if settings.MAILSHARE_ENABLE_DELETE:
            mail.delete()
            success = True

    dajax.add_data({'success':success}, 'mail_deleted')
    return dajax.json()


@dajaxice_register
def get_multibar_tags(request, selected_mails, url):
    dajax = Dajax()
    search_object = search.get_search_from_url(url)
    result = tags.mail_tags_multibar_html(search_object, selected_mails)
    dajax.add_data({'tags_html':result, 'tags_only':False, 'tags_changed':False, 'sm':selected_mails}, 'update_multibar')
    return dajax.json()
