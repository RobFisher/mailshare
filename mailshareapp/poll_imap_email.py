# License: https://github.com/RobFisher/mailshare/blob/master/LICENSE

import imaplib
import settings # TODO make this work: from django.conf import settings
import email

def fetch_messages():
    """Return a list of email.message.Message objects representing some messages in the IMAP mailbox."""
    messages = []

    server = imaplib.IMAP4_SSL(settings.MAILSHARE_IMAP_HOST)
    server.login(settings.MAILSHARE_IMAP_USER, settings.MAILSHARE_IMAP_PASSWORD)
    server.select(settings.MAILSHARE_IMAP_MAILBOX, readonly = True)
    typ, message_ids = server.search(None, 'ALL')

    # message_ids is a list with one item, so it looks like this:
    # [b'1 2 3 4 5']
    # To get a maximum number of mails we need to split it out into a list of
    # ids.
    max_emails_for_test = 10
    message_ids_to_fetch = message_ids[0].split()[0:max_emails_for_test]

    for message_id in message_ids_to_fetch:
        typ, message_data = server.fetch(message_id, '(RFC822)')
        for part in message_data:
            if isinstance(part, tuple):
                message = email.message_from_string(part[1])
                messages.append(message)

    return messages
