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

def get_html_body(email):
    """Given a mailshareapp.models.Mail object, returns the body formatted as HTML."""
    # For now assume all email bodies are HTML or plain text
    if email.content_type == 'text/html':
        return sanitise_html(email.body)
    else:
        return plaintext2html(email.body)
