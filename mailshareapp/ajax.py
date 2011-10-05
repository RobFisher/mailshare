from dajax.core import Dajax
from dajaxice.decorators import dajaxice_register
from mailshareapp.models import Mail, Contact

@dajaxice_register
def multiply(request, a, b):
    dajax = Dajax()
    result = int(a) * int(b)
    dajax.assign('#result', 'value', str(result))
    return dajax.json()

@dajaxice_register
def expand_email(request, email_id):
    dajax = Dajax()
    email_body = 'Error retrieving email'
    email = Mail.objects.get(pk=email_id)
    if(email):
        email_body = email.body
    dajax.add_data({'email_id':email_id, 'email_body':email_body}, 'set_email_body')
    return dajax.json()
