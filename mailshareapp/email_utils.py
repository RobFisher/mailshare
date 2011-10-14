# License: https://github.com/RobFisher/mailshare/blob/master/LICENSE

from mailshareapp.models import Mail
from plaintext import plaintext2html
from lxml.html.clean import Cleaner
import lxml.html.defs
import re

outlook_otags = re.compile('</*o:p>')

def sanitise_html(body):
    """Given the text of a HTML email, return HTML suitable for rendering on a web page."""
    # Discussion of sanitising HTML here:
    # http://stackoverflow.com/questions/699468/python-html-sanitizer-scrubber-filter

    # remove empty paragraphs from Outlook emails that look like <o:p>
    # or </o:p>. These were causing large line breaks between
    # paragaphs because lxml replaces them with <p></p>.
    body=outlook_otags.sub('', body)

    # Outlook emails contain span elements with style attributes. Add
    # style to the set of safe attributes allowed.
    outlook_safe_attrs = set(lxml.html.defs.safe_attrs)
    outlook_safe_attrs.add('style')
    lxml.html.defs.safe_attrs = frozenset(outlook_safe_attrs)
    cleaner = Cleaner(style=False)
    return cleaner.clean_html(body)


def mail_body_to_html(mail):
    """Given a mailshareapp.models.Mail object, returns the body formatted as HTML."""
    # For now assume all email bodies are HTML or plain text
    if mail.content_type == 'text/html':
        return sanitise_html(mail.body)
    else:
        return plaintext2html(mail.body)


def contact_to_html(contact):
    """Given a mailshareapp.models.Contact object, return a string representing it in HTML."""
    result = '<a href="/search/?sender=' + str(contact.id)
    if contact.name != '':
        result += '" title="' + contact.address + '">' + contact.name + '</a>'
    else:
        result += '">' + contact.address + '</a>'
    return result


def contacts_queryset_to_html(contacts):
    """Given a QuerySet of contacts, return a string representing them in HTML."""
    if len(contacts) == 0:
        return ''
    result = contact_to_html(contacts[0])
    for contact in contacts[1:]:
        result += ', '
        result += contact_to_html(contact)
    return result


def mail_contacts_to_html(mail):
    """Given a mailshareapp.models.Mail object, return the recipients formatted as HTML."""
    result = '<div class="recipients"><p>From: '
    result += contact_to_html(mail.sender)
    result += '<br />To: '
    result += contacts_queryset_to_html(mail.to.all())
    result += '<br />Cc: '
    result += contacts_queryset_to_html(mail.cc.all())
    result += '</p></div>'
    return result
