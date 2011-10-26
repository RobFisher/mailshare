"""Module to define the Search class."""

from django.db.models import Q
import models
import email_utils
import tags


def _get_full_text_query(s):
    return Q(subject__search=s) | Q(body__search=s)


def _get_full_text_html(s):
    return ''


def _get_full_text_url(s):
    return 'query=' + s


def _get_tag_id_query(i):
    return Q(tags__id=int(i))


def _get_tag_id_html(i):
    tag_id = int(i)
    html = 'Emails with tag '
    try:
        tag = models.Tag.objects.get(id=tag_id)
    except models.Tag.DoesNotExist:
        html += 'unknown'
    else:
        html += tags.tag_to_html(tag)
    return html


def _get_tag_id_url(i):
    return 'tag_id=' + i


def _get_sender_id_query(i):
    return Q(sender__id=int(i))


def _get_sender_id_html(i):
    sender_id = int(i)
    html = 'Emails sent by '
    try:
        sender = models.Contact.objects.get(id=sender_id)
    except models.Contact.DoesNotExist:
        html += 'unknown'
    else:
        html += email_utils.contact_to_html(sender)
    return html


def _get_sender_id_url(i):
    return 'sender=' + i


def _get_mail_id_query(i):
    return Q(id=int(i))


def _get_mail_id_html(i):
    return ''


def _get_mail_id_url(i):
    return 'mail_id=' + i


class _Parameter:
    """Operations that can be performed on a search parameter."""
    def __init__(self, get_query_func, get_html_func, get_url_func):
        self.get_query = get_query_func
        self.get_html = get_html_func
        self.get_url_param = get_url_func


_parameters_map = {
    'query': _Parameter(_get_full_text_query, _get_full_text_html, _get_full_text_url),
    'tag_id': _Parameter(_get_tag_id_query, _get_tag_id_html, _get_tag_id_url),
    'sender': _Parameter(_get_sender_id_query, _get_sender_id_html, _get_sender_id_url),
    'mail_id': _Parameter(_get_mail_id_query, _get_mail_id_html, _get_mail_id_url),
}


class Search:
    """Represents a search and can convert between various representations of a search."""
    def __init__(self, search_parameters):
        """
        Create a new search object with the specified parameters.
        
        Arguments:
        search_parameters -- A list of tuples, where each tuple is a (parameter, value) pair.

        """
        self._search_parameters = search_parameters
        self._query_set = None
        self._html = None
        self._url_path = None


    def get_query_set(self):
        """Return a Django query set associated with this search."""
        if self._query_set == None:
            q = None
            # only handle the first parameter for now
            if len(self._search_parameters) > 0:
                field_name = self._search_parameters[0][0]
                field_value = self._search_parameters[0][1]
                if field_name in _parameters_map:
                    q = _parameters_map[field_name].get_query(field_value)
            if q == None:
                self._query_set = models.Mail.objects.none()
            else:
                self._query_set = models.Mail.objects.filter(q)

        return self._query_set


    def get_html(self):
        if self._html == None:
            self._html = ''
            # only handle the first parameter for now
            if len(self._search_parameters) > 0:
                field_name = self._search_parameters[0][0]
                field_value = self._search_parameters[0][1]
                if field_name in _parameters_map:
                    self._html += _parameters_map[field_name].get_html(field_value)

        return self._html


    def get_url_path(self):
        if self._url_path == None:
            self._url_path = '/search/?'
            # only handle the first parameter for now
            if len(self._search_parameters) > 0:
                field_name = self._search_parameters[0][0]
                field_value = self._search_parameters[0][1]
                if field_name in _parameters_map:
                    self._url_path += _parameters_map[field_name].get_url_param(field_value)

        return self._url_path


def get_mail_id_search(mail_id):
    return Search([('mail_id', str(mail_id))])


def get_sender_id_search(sender_id):
    return Search([('sender', str(sender_id))])


def get_tag_id_search(tag_id):
    return Search([('tag_id', str(tag_id))])
