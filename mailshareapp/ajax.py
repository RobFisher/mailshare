from dajax.core import Dajax
from dajaxice.decorators import dajaxice_register

@dajaxice_register
def multiply(request, a, b):
    dajax = Dajax()
    dajax.alert('This is a test')
    #result = int(a) * int(b)
    #dajax.assign('#result', 'value', str(result))
    #return dajax.json()
