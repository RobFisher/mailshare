"""Module to define the Search class."""

from django.db.models import Q
import models
import email_utils
import tags


class _Parameter(object):
    def __init__(self, value):
        self.string_value = value


    def get_url_param(self):
        return self.parameter_name + '=' + self.string_value


class _FullTextParameter(_Parameter):
    parameter_name = 'query'


    def __init__(self, value):
        super(_FullTextParameter, self).__init__(value)


    def get_query(self):
        return Q(subject__search=self.string_value) | Q(body__search=self.string_value)


    def get_html(self):
        return ''


class _TagParameter(_Parameter):
    parameter_name = 'tag_id'


    def __init__(self, value):
        super(_TagParameter, self).__init__(value)
        self.tid = int(value)


    def get_query(self):
        return Q(tags__id=self.tid)


    def get_html(self):
        html = 'Emails with tag '
        try:
            tag = models.Tag.objects.get(id=self.tid)
        except models.Tag.DoesNotExist:
            html += 'unknown'
        else:
            html += tags.tag_to_html(tag)
        return html


class _ContactParameter(_Parameter):
    parameter_name = 'contact'


    def __init__(self, value):
        super(_ContactParameter, self).__init__(value)
        self.cid = int(value)


    def _get_contact_name_html(self):
        html = ''
        try:
            sender = models.Contact.objects.get(id=self.cid)
        except models.Contact.DoesNotExist:
            html += 'unknown'
        else:
            html += email_utils.contact_to_html(sender)
        return html


    def get_query(self):
        return Q(sender__id=self.cid) | Q(to__id=self.cid) | Q(cc__id=self.cid)


    def get_html(self):
        html = 'Emails to or from '
        html += self._get_contact_name_html()
        html += '[<a href="' + get_sender_id_search(self.cid).get_url_path() + '">sent</a>]'
        return html


class _SenderParameter(_ContactParameter):
    parameter_name = 'sender'


    def get_query(self):
        return Q(sender__id=self.cid)


    def get_html(self):
        html = 'Emails sent by '
        html += self._get_contact_name_html()
        html += '[<a href="' + get_contact_id_search(self.cid).get_url_path() + '">to or from</a>]'
        return html


class _MailParameter(_Parameter):
    parameter_name = 'mail_id'


    def __init__(self, value):
        super(_MailParameter, self).__init__(value)
        self.mid = int(value)


    def get_query(self):
        return Q(id=self.mid)


    def get_html(self):
        return ''


_parameters_map = {
    _FullTextParameter.parameter_name: _FullTextParameter,
    _TagParameter.parameter_name: _TagParameter,
    _ContactParameter.parameter_name: _ContactParameter,
    _SenderParameter.parameter_name: _SenderParameter,
    _MailParameter.parameter_name: _MailParameter,
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
        self._paremeter = None

        # Only handle the first parameter for now
        if len(self._search_parameters) > 0:
            field_name = self._search_parameters[0][0]
            field_value = self._search_parameters[0][1]
            if field_name in _parameters_map:
                self._parameter = _parameters_map[field_name](field_value)


    def get_query_set(self):
        """Return a Django query set associated with this search."""
        if self._query_set == None:
            q = None
            if self._parameter:
                q = self._parameter.get_query()
            if q == None:
                self._query_set = models.Mail.objects.none()
            else:
                self._query_set = models.Mail.objects.filter(q).distinct()

        return self._query_set


    def get_html(self):
        if self._html == None:
            self._html = ''
            if self._parameter:
                self._html += self._parameter.get_html()

        return self._html


    def get_url_path(self):
        if self._url_path == None:
            self._url_path = '/search/?'
            if self._parameter:
                self._url_path += self._parameter.get_url_param()

        return self._url_path


def get_mail_id_search(mail_id):
    return Search([('mail_id', str(mail_id))])


def get_sender_id_search(sender_id):
    return Search([('sender', str(sender_id))])


def get_tag_id_search(tag_id):
    return Search([('tag_id', str(tag_id))])


def get_contact_id_search(contact_id):
    return Search([('contact', str(contact_id))])
