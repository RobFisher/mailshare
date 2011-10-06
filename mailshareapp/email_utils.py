# License: https://github.com/RobFisher/mailshare/blob/master/LICENSE

from mailshareapp.models import Mail
from plaintext import plaintext2html

def get_html_body(email):
    """Given a mailshareapp.models.Mail object, returns the body formatted as HTML."""
    # For now assume all email bodies are plain text
    return plaintext2html(email.body)
