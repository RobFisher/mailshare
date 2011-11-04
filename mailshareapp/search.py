"""Module to define the Search class."""

from django.db.models import Q
import models
import email_utils
import tags


class _Parameter(object):
    def __init__(self, value, index):
        self.string_value = value
        self.index = index


    def get_url_param(self):
        url = self.parameter_name
        if self.index:
            url += '-' + str(index)
        url += '=' + self.string_value
        return url


class _FullTextParameter(_Parameter):
    parameter_name = 'query'


    def __init__(self, value, index):
        super(_FullTextParameter, self).__init__(value, index)


    def get_query(self):
        return Q(subject__search=self.string_value) | Q(body__search=self.string_value)


    def get_html(self):
        return ''


class _TagParameter(_Parameter):
    parameter_name = 'tag_id'


    def __init__(self, value, index):
        super(_TagParameter, self).__init__(value, index)
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


    def __init__(self, value, index):
        super(_ContactParameter, self).__init__(value, index)
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
        html += '[<a href="' + get_recipient_id_search(self.cid).get_url_path() + '">to</a>'
        html += '|<a href="' + get_sender_id_search(self.cid).get_url_path() + '">from</a>'
        html += '|to or from]'
        return html


class _SenderParameter(_ContactParameter):
    parameter_name = 'sender'


    def get_query(self):
        return Q(sender__id=self.cid)


    def get_html(self):
        html = 'Emails from '
        html += self._get_contact_name_html()
        html += '[<a href="' + get_recipient_id_search(self.cid).get_url_path() + '">to</a>'
        html += '|from'
        html += '|<a href="' + get_contact_id_search(self.cid).get_url_path() + '">to or from</a>]'
        return html


class _RecipientParameter(_ContactParameter):
    parameter_name = 'recipient'


    def get_query(self):
        return Q(to__id=self.cid)


    def get_html(self):
        html = 'Emails to '
        html += self._get_contact_name_html()
        html += '[to'
        html += '|<a href="' + get_sender_id_search(self.cid).get_url_path() + '">from</a>'
        html += '|<a href="' + get_contact_id_search(self.cid).get_url_path() + '">to or from</a>]'
        return html


class _MailParameter(_Parameter):
    parameter_name = 'mail_id'


    def __init__(self, value, index):
        super(_MailParameter, self).__init__(value, index)
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
    _RecipientParameter.parameter_name: _RecipientParameter,
    _MailParameter.parameter_name: _MailParameter,
}


def _get_parameter_name_and_index(field_name):
    parameter_name = field_name
    index = 0
    dash_position = field_name.rfind('-')
    if dash_position != -1:
        parameter_name = field_name[0:dash_position]
        index = int(field_name[dash_position+1:])
    return (parameter_name, index)


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
        self._parameter = None
        self._and = None

        # handle the first parameter
        if len(self._search_parameters) > 0:
            (parameter_name, parameter_index) = _get_parameter_name_and_index(self._search_parameters[0][0])
            parameter_value = self._search_parameters[0][1]
            if parameter_name in _parameters_map:
                self._parameter = _parameters_map[parameter_name](parameter_value, parameter_index)
        
        # handle any remaining parameters
        if len(self._search_parameters) > 1:
            self._and = Search(self._search_parameters[1:])


    def filter_results(self, results):
        q = None
        if self._parameter:
            q = self._parameter.get_query()
            if q:
                results = results.filter(q).distinct()
            else:
                results = models.Mail.objects.none()

        if self._and:
            results = self._and.filter_results(results)
        return results


    def get_query_set(self):
        """Return a Django query set associated with this search."""
        if self._query_set == None:
            self._query_set = self.filter_results(models.Mail.objects.all())

        return self._query_set


    def get_html(self):
        if self._html == None:
            self._html = '<p>'
            if self._parameter:
                self._html += self._parameter.get_html()
            self._html += '</p>\n'
            if self._and:
                self._html += self._and.get_html()

        return self._html


    def append_url_parameters(self, url_path):
        if self._parameter:
            url_path += self._parameter.get_url_param()
        if self._and:
            url_path = self._and.append_url_parameters(url_path)
        return url_path


    def get_url_path(self):
        if self._url_path == None:
            self._url_path = '/search/?'
            self._url_path = self.append_url_parameters(self._url_path)

        return self._url_path


def get_mail_id_search(mail_id):
    return Search([('mail_id', str(mail_id))])


def get_sender_id_search(sender_id):
    return Search([('sender', str(sender_id))])


def get_tag_id_search(tag_id):
    return Search([('tag_id', str(tag_id))])


def get_contact_id_search(contact_id):
    return Search([('contact', str(contact_id))])


def get_recipient_id_search(contact_id):
    return Search([('recipient', str(contact_id))])
