from dajax.core import Dajax
from dajaxice.decorators import dajaxice_register
from mailshareapp.models import Mail, Contact, Tag
from email_utils import *
import tags

@dajaxice_register
def expand_email(request, email_id):
    dajax = Dajax()
    email_body = 'Error retrieving email'
    email = Mail.objects.get(pk=email_id)
    if(email):
        email_body = mail_contacts_to_html(email)
        email_body += tags.mail_tags_to_html(email)
        email_body += mail_body_to_html(email)
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
def tag_completion(request, text):
    dajax = Dajax()
    tags = Tag.objects.filter(name__icontains=text)
    response = []
    for tag in tags:
        response.append(tag.name)
    print text
    print response
    dajax.add_data({'tags':response}, 'set_tag_completion')
    return dajax.json()
