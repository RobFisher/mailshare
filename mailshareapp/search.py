"""Module to define the Search class and factory functions."""

# License: https://github.com/RobFisher/mailshare/blob/master/LICENSE

import datetime
from django.db.models import Q
from django.http import QueryDict
from django.utils.http import urlquote
from django.utils.html import escape
import models
import email_utils
import tags


class _Parameter(object):
    # Represents a type of search parameter. Each type of search parameter can be
    # represented in various ways. This class also helps keep track of the index value so that
    # GET URLs can be constructed with unique parameter names.
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
        url = self.get_url_parameter_name() + '=' + urlquote(self.string_value)
        return url


    def get_remove_html(self):
        html = ''
        removal_search = self.search.remove_parameter(self.parameter_name, self.string_value)
        if removal_search:
            html += '[<a href="'
            html += removal_search.get_url_path()
            html += '">x</a>]'
        return html


    def get_option_link_html(self, option_search, option_text):
        html = '<a href="'
        new_search = self.search.replace_parameter(self, option_search._parameter)
        html += new_search.get_url_path()
        html += '">' + option_text + '</a>'
        return html


    def get_hidden_form_html(self):
        html = '<input type="hidden" name="'
        html += self.get_url_parameter_name()
        html += '" value="'
        html += escape(self.string_value)
        html += '" />'
        return html


class _FullTextParameter(_Parameter):
    parameter_name = 'query'


    def __init__(self, value, index, search):
        super(_FullTextParameter, self).__init__(value, index, search)


    def get_query(self):
        return Q(subject__search=self.string_value) | Q(body__search=self.string_value)


    def get_html(self):
        html = 'Emails matching text query: <a href="'
        html += get_full_text_search(self.string_value).get_url_path()
        html += '">' + self.string_value + '</a>'
        html += ' ' + self.get_remove_html()
        return html


class _TagParameter(_Parameter):
    parameter_name = 'tag_id'


    def __init__(self, value, index, search):
        super(_TagParameter, self).__init__(value, index, search)
        self.tid = int(value)


    def get_query(self):
        return Q(tags__id=self.tid)


    def get_tag_name_html(self):
        try:
            tag = models.Tag.objects.get(id=self.tid)
        except models.Tag.DoesNotExist:
            html = 'unknown'
        else:
            html = tags.tag_to_html(tag)
        return html


    def get_html(self):
        html = 'Emails with tag '
        html += self.get_tag_name_html()
        html += '<br />[with|' + self.get_option_link_html(get_ntag_id_search(self.tid), 'without') + ']'
        html += self.get_remove_html()
        return html


class _NotTagParameter(_TagParameter):
    parameter_name = 'ntag_id'


    def get_query(self):
        return (~Q(tags__id=self.tid))


    def get_html(self):
        html = 'Emails without tag '
        html += self.get_tag_name_html()
        html += '<br />[' + self.get_option_link_html(get_tag_id_search(self.tid), 'with') + '|without]'
        html += self.get_remove_html()
        return html


class _ContactParameter(_Parameter):
    parameter_name = 'contact'


    def __init__(self, value, index, search):
        super(_ContactParameter, self).__init__(value, index, search)
        self.cid = int(value)


    def get_contact_name_html(self):
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
        html += self.get_contact_name_html()
        html += '<br />[' + self.get_option_link_html(get_recipient_id_search(self.cid), 'to')
        html += '|' + self.get_option_link_html(get_sender_id_search(self.cid), 'from')
        html += '|to or from]'
        html += self.get_remove_html()
        return html


class _SenderParameter(_ContactParameter):
    parameter_name = 'sender'


    def get_query(self):
        return Q(sender__id=self.cid)


    def get_html(self):
        html = 'Emails from '
        html += self.get_contact_name_html()
        html += '<br />[' + self.get_option_link_html(get_recipient_id_search(self.cid), 'to')
        html += '|from'
        html += '|' + self.get_option_link_html(get_contact_id_search(self.cid), 'to or from')
        html += ']'

        html += self.get_remove_html()
        return html


class _RecipientParameter(_ContactParameter):
    parameter_name = 'recipient'


    def get_query(self):
        return Q(to__id=self.cid) | Q(cc__id=self.cid)


    def get_html(self):
        html = 'Emails to '
        html += self.get_contact_name_html()
        html += '<br />[to'
        html += '|' + self.get_option_link_html(get_sender_id_search(self.cid), 'from')
        html += '|' + self.get_option_link_html(get_contact_id_search(self.cid), 'to or from')
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
        html += ' ' + self.get_remove_html()
        return html


class _AgeInDaysParameter(_Parameter):
    parameter_name = 'days'


    def __init__(self, value, index, search):
        super(_AgeInDaysParameter, self).__init__(value, index, search)
        self.days = int(value)


    def get_query(self):
        # We want to do this:
        # start_date = datetime.date.today()-datetime.timedelta(self.days)
        # return Q(date__gte=start_date)
        #
        # But there is a bug in MySQL which causes this error:
        # Truncated incorrect DOUBLE value.
        #
        # Instead we use this workaround in filter_query_set below:
        # https://code.djangoproject.com/ticket/7074#comment:13
        #
        # The MySQL bug is fixed in 5.5.0 but in Ubuntu 10.04 LTS we have 5.1.41.
        # http://bugs.mysql.com/bug.php?id=34374
        return None


    def filter_query_set(self, query_set):
        # See comments in get_query, above, for why this method exists
        start_date = datetime.date.today()-datetime.timedelta(self.days)
        result = query_set.extra(where=['date >= DATE(%s)'], params=[start_date])
        return result


    def get_html(self):
        html = 'Emails from the last ' + self.string_value + ' day'
        if self.days != 1:
            html += 's [' + self.get_option_link_html(get_days_search(1), 'day')
        else:
            html += ' [day'
        if self.days != 7:
            html += '|' + self.get_option_link_html(get_days_search(7), 'week')
        else:
            html += '|week'
        if self.days != 30:
            html += '|' + self.get_option_link_html(get_days_search(30), 'month')
        else:
            html += '|month'
        if self.days != 365:
            html += '|' + self.get_option_link_html(get_days_search(365), 'year')
        else:
            html += '|year'
        html += ']'
        html += self.get_remove_html()
        return html


# When parsing a URL, we want to create Parameter objects of different sub-classes
# depending on the name in the URL.
_parameters_map = {
    _FullTextParameter.parameter_name: _FullTextParameter,
    _TagParameter.parameter_name: _TagParameter,
    _NotTagParameter.parameter_name: _NotTagParameter,
    _ContactParameter.parameter_name: _ContactParameter,
    _SenderParameter.parameter_name: _SenderParameter,
    _RecipientParameter.parameter_name: _RecipientParameter,
    _MailParameter.parameter_name: _MailParameter,
    _AgeInDaysParameter.parameter_name: _AgeInDaysParameter,
}


def _get_parameter_name_and_index(field_name):
    # In a GET request, all the parameter names must be unique. So we append a hyphen and
    # an index number to the root name. Here we parse out the name and index.
    parameter_name = field_name
    index = 0
    dash_position = field_name.rfind('-')
    if dash_position != -1:
        parameter_name = field_name[0:dash_position]
        index = int(field_name[dash_position+1:])
    return (parameter_name, index)


def _expand_search_parameters(search_parameters):
    # convert a list of (name-index, value) tuples into (name, index, value)
    result = []
    for (key, value) in search_parameters:
        (name, index) = _get_parameter_name_and_index(key)
        # filter out recipient=0 searches which result from selecting "All" teams
        if name != 'recipient' or value != '0':
            result.append((name, index, value))
    return result


def _expand_and_sort_search_parameters(search_parameters):
    # The initialiser for the Search class can take a list if (name-index, value) tuples or
    # (name, index, value) tuples. This makes sure we have the latter, and also sorts the
    # list by index, which helps things stay in the same order in the UI.
    if len(search_parameters[0]) < 3:
        search_parameters = _expand_search_parameters(search_parameters)
    result = sorted(search_parameters, key=lambda param: param[1])
    return result


class Search:
    """
    Represents a search and can convert between various representations of a search.

    By representing a search as an object we can represent it as a URL in the user's browser and
    as a Django query set representing the search results. We can also generate HTML to display
    information about the search to the user.

    A Search object is typically created from a GET request. We parse the parameters to construct
    the search. Currently, search parameters can only be ANDed together.

    When using the public interface a Search object behaves as if it were immutable. There are methods
    for generating new Search objects based on this one, which have search parameters added, removed
    or modified. In this way we can generate URIs that link to new searches based on the current one.
    Some of these methods take Search objects as parameters. To create Search objects to pass into these
    methods, use the get_..._search factory functions.

    """
    def __init__(self, search_parameters, _root_search=None, _skip_sort=False):
        """
        Create a new search object with the specified parameters.
        
        Arguments:
        search_parameters -- A list of tuples, where each tuple is either (parameter-index, value) or
                             (parameter, index, value). The former is useful as it is what we get from
                             Django's request.GET.items(). For other uses it is more convenient to use
                             the get_..._search() factory functions.

        """
        self._query_set = None
        self._html = None
        self._hidden_form_html = None
        self._url_path = None
        self._parameter = None

        # Each Search object manages only one _Parameter object. To AND together several parameters,
        # we recursively link to more Search objects.
        self._and = None
        self.root_search = self

        if _root_search != None:
            self.root_search = _root_search

        if not _skip_sort:
            search_parameters = _expand_and_sort_search_parameters(search_parameters)

        # handle the first parameter
        if len(search_parameters) > 0:
            (name, index, value) = search_parameters[0]
            if name in _parameters_map:
                self._parameter = _parameters_map[name](value, index, self.root_search)
        
        # handle any remaining parameters
        if len(search_parameters) > 1:
            self._and = Search(search_parameters[1:], self.root_search, True)


    def _filter_results(self, results):
        # Apply the filter for our _Parameter object and recursively apply the filter for ANDed parameters.
        q = None
        if self._parameter:
            q = self._parameter.get_query()
            if q:
                results = results.filter(q).distinct()
            else:
                results = self._parameter.filter_query_set(results)

        if self._and:
            results = self._and._filter_results(results)
        return results


    def get_query_set(self):
        """Return a Django query set representing the results of this search."""
        if self._query_set == None:
            self._query_set = self._filter_results(models.Mail.objects.all())

        return self._query_set


    def get_html(self):
        """Return HTML representing the parameters of this search."""
        if self._html == None:
            self._html = '<p>'
            if self._parameter:
                self._html += self._parameter.get_html()
            self._html += '</p>\n'
            if self._and:
                self._html += self._and.get_html()

        return self._html


    def get_hidden_form_html(self):
        """Return HTML representing hidden form items that represent the current search and will recreate it with a GET request."""
        if self._hidden_form_html == None:
            self._hidden_form_html = ''
            if self._parameter:
                self._hidden_form_html += self._parameter.get_hidden_form_html()
            if self._and:
                self._hidden_form_html += self._and.get_hidden_form_html()

        return self._hidden_form_html


    def get_form_query_name(self):
        """Return the name of the text box to use in a search form that will generate a search with a new full text query appended to this one."""
        next_index = self.get_highest_index() + 1
        return 'query-' + str(next_index)


    def _append_url_parameters(self, url_path):
        # recurse through ANDed searches to construct the URL path
        if self._parameter:
            url_path += self._parameter.get_url_param()
        if self._and:
            url_path += '&'
            url_path = self._and._append_url_parameters(url_path)
        return url_path


    def get_url_path(self):
        """Return a URL path that links to this search."""
        if self._url_path == None:
            self._url_path = '/search/?'
            self._url_path = self._append_url_parameters(self._url_path)

        return self._url_path


    def _copy(self, root_search=None):
        # Create a copy of this search. Using this we avoid modifying existing Search objects, so that
        # they appear immutable.
        new_search = Search( \
            [(self._parameter.parameter_name, self._parameter.index, self._parameter.string_value)], root_search)
        if self._and:
            new_search._and = self._and._copy(new_search.root_search)
        return new_search


    def add_and(self, search):
        """Return a new Search equal to this Search AND the specified Search."""
        new_search = self._copy()
        new_search._add_and(search)
        return new_search


    def _add_and(self, search):
        # AND the specified Search object with this search. We recurse through the _and chain and add
        # the new search to the end.
        if self._and:
            self._and._add_and(search)
        else:
            highest_index = self.get_highest_index()
            search._parameter.index = highest_index + 1
            search.root_search = self.root_search
            self._and = search


    def remove_parameter(self, name, value):
        """Return a new Search equal to this Search with the matching parameter removed."""
        new_search = self._copy()
        new_search = new_search._remove_parameter(name, value)
        return new_search


    def _remove_parameter(self, name, value):
        # Search through the _and chain for the specified parameter and remove it.
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
        """
        Return a new Search with equal to this search but with old_parameter replaced with new_parameter.

        The parameter replaced is the one whose index is the same as old_paramete's.

        """
        new_search = self._copy()
        new_search._replace_parameter( \
            old_parameter, new_parameter.parameter_name, new_parameter.string_value, \
                old_parameter.index)
        return new_search


    def _replace_parameter(self, old_parameter, name, value, index):
        # Search through the _and chain for the old parameter and replace it.
        if old_parameter.index == self._parameter.index:
            new_parameter = _parameters_map[name](value, index, self.root_search)
            self._parameter = new_parameter
        elif self._and:
            self._and._replace_parameter(old_parameter, name, value, index)


    def get_highest_index(self):
        """Return the current highest index. Useful when adding new parameters which need a unique index."""
        return self.root_search._get_highest_index()


    def _get_highest_index(self, highest_so_far=0):
        # Recurse through the _and chain to find the highest index.
        if self._parameter.index > highest_so_far:
            highest_so_far = self._parameter.index
        if self._and:
            highest_so_far = self._and._get_highest_index(highest_so_far)
        return highest_so_far


def get_full_text_search(query):
    """Return a new Search object representing a full text search for the specified string."""
    return Search([(_FullTextParameter.parameter_name, query)])


def get_mail_id_search(mail_id):
    """Return a new Search object representing a search for a mail with the specified id."""
    return Search([(_MailParameter.parameter_name, str(mail_id))])


def get_sender_id_search(sender_id):
    """Return a new Search object representing a search for mails with the specified sender."""
    return Search([(_SenderParameter.parameter_name, str(sender_id))])


def get_tag_id_search(tag_id):
    """Return a new Search object representing a search for mails with the specified tag."""
    return Search([(_TagParameter.parameter_name, str(tag_id))])


def get_ntag_id_search(tag_id):
    """Return a new Search object representing a search for mails that do not have the specified tag."""
    return Search([(_NotTagParameter.parameter_name, str(tag_id))])


def get_contact_id_search(contact_id):
    """Return a new Search object representing a search for mails sent or received by the specified contact."""
    return Search([(_ContactParameter.parameter_name, str(contact_id))])


def get_recipient_id_search(contact_id):
    """Return a new Search object representing a search for mails received by the specified contact."""
    return Search([(_RecipientParameter.parameter_name, str(contact_id))])


def get_days_search(days):
    """Return new Search object representing a search for emails received in the last days days."""
    return Search([(_AgeInDaysParameter.parameter_name, str(days))])


def get_team_search(contact_id, days):
    """Return new Search object representing a search for mails sent to the specified contact in the last days days."""
    return Search([(_RecipientParameter.parameter_name, str(contact_id)), (_AgeInDaysParameter.parameter_name, str(days))])


def get_search_from_url(url):
    """Return a new Search object described by the specified GET request URL."""
    url_parameters = url[url.rfind('?')+1:]
    qd = QueryDict(url_parameters)
    return Search(qd.items())
