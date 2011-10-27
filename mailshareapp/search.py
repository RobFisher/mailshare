"""Module to define the Search class."""

from django.db.models import Q
from mailshareapp.models import Mail, Contact, Tag

def _get_int(request, parameter):
    """Returns an int from a GET request if available, otherwise returns -1"""
    result = -1
    if parameter in request.GET:
        try:
            result = int(request.GET[parameter])
        except ValueError:
            pass
    return result


def _get_string(request, parameter):
    """Returns a string from a GET request if available, otherwise returns ''"""
    result = ''
    if parameter in request.GET:
        result = request.GET[parameter]
    return result


def _get_full_text_query(s):
    return Q(subject__search=s) | Q(body__search=s)


def _get_tag_id_query(i):
    return Q(tags__id=int(i))


def _get_sender_id_query(i):
    return Q(sender__id=int(i))


def _get_mail_id_query(i):
    return Q(id=int(i))


_parameters_map = {
    'query': _get_full_text_query,
    'tag_id': _get_tag_id_query,
    'sender': _get_sender_id_query,
    'mail_id': _get_mail_id_query,
}


class Search:
    def __init__(self, request):
        """Create a new search object based on the specified request object."""
        self.query = None;

        # only handle the first parameter for now
        request_items = request.GET.items()
        if len(request_items) > 0:
            if request_items[0][0] in _parameters_map:
                self.query = _parameters_map[request_items[0][0]](request_items[0][1])

        if self.query != None:
            self.results = Mail.objects.filter(self.query)
        else:
            self.results = Mail.objects.none()
