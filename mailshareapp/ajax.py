from dajax.core import Dajax
from dajaxice.decorators import dajaxice_register
from mailshareapp.models import Mail, Contact
from email_utils import get_html_body

@dajaxice_register
def expand_email(request, email_id):
    dajax = Dajax()
    email_body = 'Error retrieving email'
    email = Mail.objects.get(pk=email_id)
    if(email):
        email_body = get_html_body(email)
    dajax.add_data({'email_id':email_id, 'email_body':email_body}, 'set_email_body')
    return dajax.json()
