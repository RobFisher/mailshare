"""Module to define the Search class."""

from django.db.models import Q
from django.http import QueryDict
import models
import email_utils
import tags


class _Parameter(object):
    def __init__(self, value, index, search):
        self.string_value = value
        self.index = index
        self.search = search

    
    def get_url_parameter_name(self):
        url = self.parameter_name
        if self.index:
            url += '-' + str(self.index)
        return url


    def get_url_param(self):
        url = self.get_url_parameter_name() + '=' + self.string_value
        return url


    def get_remove_html(self):
        html = ''
        removal_search = self.search.remove_parameter(self.parameter_name, self.string_value)
        if removal_search:
            html += '[<a href="'
            html += removal_search.get_url_path()
            html += '">x</a>]'
        return html


    def get_hidden_form_html(self):
        html = '<input type="hidden" name="'
        html += self.get_url_parameter_name()
        html += '" value="'
        html += self.string_value
        html += '" />'
        return html


class _FullTextParameter(_Parameter):
    parameter_name = 'query'


    def __init__(self, value, index, search):
        super(_FullTextParameter, self).__init__(value, index, search)


    def get_query(self):
        return Q(subject__search=self.string_value) | Q(body__search=self.string_value)


    def get_html(self):
        html = 'Emails matching text query: ' + self.string_value
        html += self.get_remove_html()
        return html


class _TagParameter(_Parameter):
    parameter_name = 'tag_id'


    def __init__(self, value, index, search):
        super(_TagParameter, self).__init__(value, index, search)
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
        html += self.get_remove_html()
        return html


class _ContactParameter(_Parameter):
    parameter_name = 'contact'


    def __init__(self, value, index, search):
        super(_ContactParameter, self).__init__(value, index, search)
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


    def _get_option_link_html(self, option_search, option_text):
        html = '<a href="'
        new_search = self.search.replace_parameter(self, option_search._parameter)
        html += new_search.get_url_path()
        html += '">' + option_text + '</a>'
        return html


    def get_query(self):
        return Q(sender__id=self.cid) | Q(to__id=self.cid) | Q(cc__id=self.cid)


    def get_html(self):
        html = 'Emails to or from '
        html += self._get_contact_name_html()
        html += '[' + self._get_option_link_html(get_recipient_id_search(self.cid), 'to')
        html += '|' + self._get_option_link_html(get_sender_id_search(self.cid), 'from')
        html += '|to or from]'
        html += self.get_remove_html()
        return html


class _SenderParameter(_ContactParameter):
    parameter_name = 'sender'


    def get_query(self):
        return Q(sender__id=self.cid)


    def get_html(self):
        html = 'Emails from '
        html += self._get_contact_name_html()
        html += '[' + self._get_option_link_html(get_recipient_id_search(self.cid), 'to')
        html += '|from'
        html += '|' + self._get_option_link_html(get_contact_id_search(self.cid), 'to or from')
        html += ']'

        html += self.get_remove_html()
        return html


class _RecipientParameter(_ContactParameter):
    parameter_name = 'recipient'


    def get_query(self):
        return Q(to__id=self.cid)


    def get_html(self):
        html = 'Emails to '
        html += self._get_contact_name_html()
        html += '[to'
        html += '|' + self._get_option_link_html(get_sender_id_search(self.cid), 'from')
        html += '|' + self._get_option_link_html(get_contact_id_search(self.cid), 'to or from')
        html += ']'

        html += self.get_remove_html()
        return html


class _MailParameter(_Parameter):
    parameter_name = 'mail_id'


    def __init__(self, value, index, search):
        super(_MailParameter, self).__init__(value, index, search)
        self.mid = int(value)


    def get_query(self):
        return Q(id=self.mid)


    def get_html(self):
        html = 'Email with unique id ' + self.string_value
        html += self.get_remove_html()
        return html


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
    def __init__(self, search_parameters, root_search=None):
        """
        Create a new search object with the specified parameters.
        
        Arguments:
        search_parameters -- A list of tuples, where each tuple is a (parameter, value) pair.

        """
        self._query_set = None
        self._html = None
        self._hidden_form_html = None
        self._url_path = None
        self._parameter = None
        self._and = None
        self.root_search = self

        if root_search != None:
            self.root_search = root_search

        # handle the first parameter
        if len(search_parameters) > 0:
            (parameter_name, parameter_index) = _get_parameter_name_and_index(search_parameters[0][0])
            parameter_value = search_parameters[0][1]
            if parameter_name in _parameters_map:
                self._parameter = _parameters_map[parameter_name](parameter_value, parameter_index, self.root_search)
        
        # handle any remaining parameters
        if len(search_parameters) > 1:
            self._and = Search(search_parameters[1:], self.root_search)


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


    def get_hidden_form_html(self):
        if self._hidden_form_html == None:
            self._hidden_form_html = ''
            if self._parameter:
                self._hidden_form_html += self._parameter.get_hidden_form_html()
            if self._and:
                self._hidden_form_html += self._and.get_hidden_form_html()

        return self._hidden_form_html


    def get_form_query_name(self):
        next_index = self.get_highest_index() + 1
        return 'query-' + str(next_index)


    def append_url_parameters(self, url_path):
        if self._parameter:
            url_path += self._parameter.get_url_param()
        if self._and:
            url_path += '&'
            url_path = self._and.append_url_parameters(url_path)
        return url_path


    def get_url_path(self):
        if self._url_path == None:
            self._url_path = '/search/?'
            self._url_path = self.append_url_parameters(self._url_path)

        return self._url_path


    def _copy(self, root_search=None):
        new_search = Search( \
            [(self._parameter.parameter_name + '-' + str(self._parameter.index), self._parameter.string_value)], root_search)
        if self._and:
            new_search._and = self._and._copy(new_search.root_search)
        return new_search


    def add_and(self, search):
        new_search = self._copy()
        new_search._add_and(search)
        return new_search


    def _add_and(self, search):
        if self._and:
            self._and._add_and(search)
        else:
            highest_index = self.get_highest_index()
            search._parameter.index = highest_index + 1
            search.root_search = self.root_search
            self._and = search


    def remove_parameter(self, name, value):
        new_search = self._copy()
        new_search = new_search._remove_parameter(name, value)
        return new_search


    def _remove_parameter(self, name, value):
        if name == self._parameter.parameter_name and \
                value == self._parameter.string_value:
            return self._and
        if self._and:
            if name == self._and._parameter.parameter_name and \
                    value == self._and._parameter.string_value:
                self._and = self._and._and
                return self
            else:
                self._and._remove_parameter(name, value)
        return self


    def replace_parameter(self, old_parameter, new_parameter):
        new_search = self._copy()
        new_search._replace_parameter( \
            old_parameter, new_parameter.parameter_name, new_parameter.string_value, \
                old_parameter.index)
        return new_search


    def _replace_parameter(self, old_parameter, name, value, index):
        if old_parameter.index == self._parameter.index:
            new_parameter = _parameters_map[name](value, index, self.root_search)
            self._parameter = new_parameter
        elif self._and:
            self._and._replace_parameter(old_parameter, name, value, index)


    def get_highest_index(self):
        return self.root_search._get_highest_index()


    def _get_highest_index(self, highest_so_far=0):
        if self._parameter.index > highest_so_far:
            highest_so_far = self._parameter.index
        if self._and:
            highest_so_far = self._and._get_highest_index(highest_so_far)
        return highest_so_far


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


def get_search_from_url(url):
    url_parameters = url[url.rfind('?')+1:]
    qd = QueryDict(url_parameters)
    return Search(qd.items())
