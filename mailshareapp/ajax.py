import datetime
import logging
from dajax.core import Dajax
from dajaxice.decorators import dajaxice_register
from mailshareapp.models import Mail, Contact, Tag
from email_utils import *
from views import get_expanded_html
import tags

@dajaxice_register
def expand_email(request, email_id):
    dajax = Dajax()
    email_body = 'Error retrieving email'
    email = Mail.objects.get(pk=email_id)
    if(email):
        email_body=get_expanded_html(email)
    dajax.add_data({'email_id':email_id, 'email_body':email_body}, 'set_email_body')
    return dajax.json()


@dajaxice_register
def add_tag(request, email_id, tag):
    dajax = Dajax()
    mails = Mail.objects.filter(id=email_id)
    if len(mails) > 0:
        t = tags.get_or_create_tag(tag)
        mails[0].tags.add(t)
    tags_html = tags.mail_tags_to_html_list(mails[0])
    dajax.add_data({'email_id':email_id, 'tags_html':tags_html}, 'update_tags')
    return dajax.json()


@dajaxice_register
def delete_tag(request, email_id, tag_id):
    dajax = Dajax()
    try:
        mail = Mail.objects.get(id=email_id)
        tag = Tag.objects.get(id=tag_id)
    except (Mail.DoesNotExist, Mail.MultipleObjectsReturned, Tag.DoesNotExist, Tag.MultipleObjectsReturned):
        pass
    else:
        mail.tags.remove(tag)
        tags_html = tags.mail_tags_to_html_list(mail)
        tags_html += tags.undo_delete_html(mail, tag)
        dajax.add_data({'email_id':email_id, 'tags_html':tags_html}, 'update_tags')
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
