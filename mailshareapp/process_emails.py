# License: https://github.com/RobFisher/mailshare/blob/master/LICENSE

import email
import datetime
import warnings
import sys
import time
import poll_imap_email
from mailshare.mailshareapp.models import Mail, Contact, Tag
from tags import add_autotags_to_mail

def get_body(message):
    """Search all the MIME parts of the and return a tuple consisting of the content type and text of the body.
       message: an object of type email.message.Message"""
    body_part = None
    content_type = ''
    for part in message.walk():
        # best case is 'text/html'. For now assume the first of these is what we want.
        content_type = part.get_content_type()
        if  content_type == 'text/html':
            body_part = part
            # we've found it. Get out of here!
            break

        # settle for the first non-multipart payload in case there is no text/plain,
        # but keep looking
        if body_part == None and not part.is_multipart():
            body_part = part

    # decode any Base64 and convert to utf-8 if needed
    body_part_payload = ''
    if body_part:
        body_part_payload = body_part.get_payload(decode=True)
        charset = body_part.get_content_charset()
        if charset != None and charset != 'utf-8':
            body_part_payload = body_part_payload.decode(charset).encode('utf-8')

    return (content_type, body_part_payload)


def get_or_add_contact(name, address):
    """
    Looks up the email address in the Contact table. If the address does not exist in the table
    it is added. In both cases the matching Contact object is returned.

    Email addresses are considered to be case insensitive for now. While not strictly true,
    this seems more useful than the alternative.
    """
    contact_list = Contact.objects.filter(address__iexact=address)
    result = None
    if len(contact_list) == 0:
        contact = Contact(name=name, address=address)
        contact.save()
        result = contact
    else:
        result = contact_list[0]
    return result


def add_contacts_to_mail(address_field, address_headers):
    """
    Parse out email addresses and add them to the Mail table.
    address_field: a ManyToManyField linked to the Contact table
    address_header: headers retrieved with email.email.Message.get_all
    """
    if address_headers != None:
        addresses = email.utils.getaddresses(address_headers)
        for (name, address) in addresses:
            contact = get_or_add_contact(name, address)
            address_field.add(contact)


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


def get_if_present(message, header):
    """If the email header specified by header is present in message, return its value."""
    value = message.get(header)
    if value == None:
        value = ''
    return value


def add_message_to_database(message):
    """Add the message to the database if it is unique according to its Message-ID field."""
    message_id = message.get('Message-ID')
    matching_messages = Mail.objects.filter(message_id__exact=message_id)
    if len(matching_messages) == 0:
        m = Mail()
        m.sender = get_or_add_contact(*email.utils.parseaddr(message.get('from')))
        m.subject = message.get('Subject')
        m.date = datetime_from_email_date(message.get('Date'))
        m.message_id = get_if_present(message, 'Message-ID')
        m.thread_index = get_if_present(message, 'Thread-Index')
        m.in_reply_to = get_if_present(message, 'In-Reply-To')
        m.references = get_if_present(message, 'References')
        (m.content_type, m.body) = get_body(message)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            m.save()
        add_contacts_to_mail(m.to, message.get_all('to'))
        add_contacts_to_mail(m.cc, message.get_all('cc'))
        add_autotags_to_mail(m)


def print_message_headers(message):
    """Given an email.message.Message object, print out some interesting headers."""
    print "To: " + message.get('To')
    print "From: " + message.get('From')
    print "Subject: " + message.get('Subject')
    print "Date: " + message.get('Date')

mail_file_name = 'mailfile'

def quick_test(from_file=False):
    messages = None
    if from_file:
        mail_file = open(mail_file_name, 'r')
        messages = poll_imap_email.read_messages(mail_file)
    else:
        mail_file = open(mail_file_name, 'a')
        messages = poll_imap_email.fetch_messages(10, mail_file)
    for message in messages:
        add_message_to_database(message)

def test_email(n):
    """Test the nth email in the file."""
    mail_file = open(mail_file_name, 'r')
    messages = poll_imap_email.read_messages(mail_file)
    print_message_headers(messages[n])
    (content_type, body) = get_body(messages[n])
    print "Content type: " + content_type
    print body
    return messages[n]

def poll_emails(verbose=False):
    mail_file = open(mail_file_name, 'a')
    while True:
        messages = poll_imap_email.fetch_messages(10, mail_file, True)
        for message in messages:
            if verbose:
                print_message_headers(message)
            add_message_to_database(message)
        time.sleep(10)

if __name__ == '__main__':
    verbose = False
    if len(sys.argv) > 1 and sys.argv[1] == '-v':
        verbose = True
    poll_emails(verbose)
