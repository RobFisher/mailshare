# License: https://github.com/RobFisher/mailshare/blob/master/LICENSE

import email
import datetime
import poll_imap_email
from mailshare.mailshareapp.models import Mail, Addressee

def get_plain_body(message):
    """Search all the MIME parts of the email.message.Message and return the plain text body."""
    plain_body = None
    for part in message.walk():
        # for now we assume the first "text/plain" part is what we want
        if part.get_content_type() == 'text/plain':
            plain_body = part.get_payload()
            # we've found it. Get out of here!
            break

        # settle for the first non-multipart payload in case there is no text/plain,
        # but keep looking
        if not part.is_multipart():
            plain_body = part.get_payload()

    return plain_body


def get_or_add_addressee(address):
    """
    Accepts address fields from an email header of the form 'Name <email@address>'. Looks
    up the email address in the Addressee table. If the address does not exist in the table
    it is added. In all both cases the matching Addressee object is returned.

    Email addresses are considered to be case insensitive for now. While not strictly true,
    this seems more useful than the alternative.
    """
    (address_name, address_address) = email.utils.parseaddr(address)
    addressee_list = Addressee.objects.filter(address__iexact=address)
    result = None
    if len(addressee_list) == 0:
        addressee = Addressee(name=address_name, address=address_address)
        addressee.save()
        result = addressee
    else:
        result = addressee_list[0]
    return result


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
        m.sender = get_or_add_addressee(message.get('From'))
        m.subject = message.get('Subject')
        m.date = datetime_from_email_date(message.get('Date'))
        m.message_id = message.get('Message-ID')
        m.thread_index = message.get('Thread-Index')
        m.body = get_plain_body(message)
        m.save()
        addresses = message.get_all('to')
        if addresses != None:
            for address in message.get_all('to'):
                m.to.add(get_or_add_addressee(address))
        addresses = message.get_all('cc')
        if addresses != None:
            for address in message.get_all('cc'):
                m.cc.add(get_or_add_addressee(address))


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
