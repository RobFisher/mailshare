# License: https://github.com/RobFisher/mailshare/blob/master/LICENSE

import email
import datetime
import warnings
import poll_imap_email
from mailshare.mailshareapp.models import Mail, Addressee

def get_plain_body(message):
    """Search all the MIME parts of the email.message.Message and return the plain text body."""
    plain_part = None
    for part in message.walk():
        # for now we assume the first "text/plain" part is what we want
        if part.get_content_type() == 'text/plain':
            plain_part = part
            # we've found it. Get out of here!
            break

        # settle for the first non-multipart payload in case there is no text/plain,
        # but keep looking
        if part == None and not part.is_multipart():
            plain_part = part

    # decode any Base64 and convert to utf-8 if needed
    plain_part_payload = None
    if plain_part:
        plain_part_payload = plain_part.get_payload(decode=True)
        charset = plain_part.get_content_charset()
        if charset != None and charset != 'utf-8':
            plain_part_payload = plain_part_payload.decode(charset).encode('utf-8')

    return plain_part_payload


def get_or_add_addressee(name, address):
    """
    Looks up the email address in the Addressee table. If the address does not exist in the table
    it is added. In both cases the matching Addressee object is returned.

    Email addresses are considered to be case insensitive for now. While not strictly true,
    this seems more useful than the alternative.
    """
    addressee_list = Addressee.objects.filter(address__iexact=address)
    result = None
    if len(addressee_list) == 0:
        addressee = Addressee(name=name, address=address)
        addressee.save()
        result = addressee
    else:
        result = addressee_list[0]
    return result


def add_addressees_to_mail(address_field, address_headers):
    """
    Parse out email addresses and add them to the Mail table.
    address_field: a ManyToManyField linked to the Addressee table
    address_header: headers retrieved with email.email.Message.get_all
    """
    if address_headers != None:
        addresses = email.utils.getaddresses(address_headers)
        for (name, address) in addresses:
            addressee = get_or_add_addressee(name, address)
            address_field.add(addressee)


def datetime_from_email_date(email_date):
    """
    Returns a Python datetime object suitable for storing in the database given
    the email Date header string. These should comply with this specification:
    http://cr.yp.to/immhf/date.html
    """
    d = email.utils.parsedate_tz(email_date)
    dt = datetime.datetime(*d[0:6])

    # now we need to subtract the time zone offset to get a UTC time
    tz_offset = datetime.timedelta(seconds=d[9])
    dt = dt - tz_offset
    return dt


def add_message_to_database(message):
    """Add the message to the database if it is unique according to its Message-ID field."""
    message_id = message.get('Message-ID')
    matching_messages = Mail.objects.filter(message_id__exact=message_id)
    if len(matching_messages) == 0:
        m = Mail()
        m.sender = get_or_add_addressee(*email.utils.parseaddr(message.get('from')))
        m.subject = message.get('Subject')
        m.date = datetime_from_email_date(message.get('Date'))
        m.message_id = message.get('Message-ID')
        m.thread_index = message.get('Thread-Index')
        if m.thread_index == None:
            m.thread_index = ''
        m.body = get_plain_body(message)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            m.save()
        add_addressees_to_mail(m.to, message.get_all('to'))
        add_addressees_to_mail(m.cc, message.get_all('cc'))


def print_message_headers(message):
    """Given an email.message.Message object, print out some interesting headers."""
    print "To: " + message.get('To')
    print "From: " + message.get('From')
    print "Subject: " + message.get('Subject')
    print "Date: " + message.get('Date')


def quick_test():
    messages = poll_imap_email.fetch_messages()
    for message in messages:
        add_message_to_database(message)


if __name__ == '__main__':
    messages = poll_imap_email.fetch_messages()
    for message in messages:
        print_message_headers(message)
        plain_body = get_plain_body(message)
        print("-----")
        print(plain_body)
        print("-----")
        print("")
