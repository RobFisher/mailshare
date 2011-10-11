# License: https://github.com/RobFisher/mailshare/blob/master/LICENSE

import imaplib
import settings # TODO make this work: from django.conf import settings
import email

def fetch_messages(max_messages=10, output_file=None, expunge=False):
    """Return a list of email.message.Message objects representing some messages in the IMAP mailbox.
    max_messages: the maximum number of messages to fetch this call
    output_file:  a file to append email data to
    """
    messages = []

    server = imaplib.IMAP4_SSL(settings.MAILSHARE_IMAP_HOST)
    server.login(settings.MAILSHARE_IMAP_USER, settings.MAILSHARE_IMAP_PASSWORD)
    server.select(settings.MAILSHARE_IMAP_MAILBOX, readonly = True)
    typ, message_ids = server.search(None, 'ALL')

    # message_ids is a list with one item, so it looks like this:
    # [b'1 2 3 4 5']
    # To get a maximum number of mails we need to split it out into a list of
    # ids.
    message_ids_to_fetch = message_ids[0].split()[0:max_messages]

    for message_id in message_ids_to_fetch:
        typ, message_data = server.fetch(message_id, '(RFC822)')
        for part in message_data:
            if isinstance(part, tuple):
                if output_file != None:
                    write_part(output_file, part[1])
                message = email.message_from_string(part[1])
                messages.append(message)
        if expunge and settings.MAILSHARE_IMAP_ENABLE_EXPUNGE:
            typ, response = server.store(message_id, '+FLAGS', '\\Deleted')
            typ, response = server.expunge()

    return messages


def write_part(output_file, message_data):
    """Write the email part to the file."""
    output_file.write(str(len(message_data))+'\n')
    output_file.write(message_data)
    output_file.write('\n')


def read_messages(input_file):
    """
    Read up to max_messages messages from input_file. Reads messages previously written to the
    output_file specified in a call to fetch_messages. This enable replaying of messages into the
    database that have been deleted from the IMAP mailbox.
    """
    messages = []
    while True:
        line = input_file.readline()
        if line == '':
            break
        length = int(line)
        message_data = input_file.read(length)
        input_file.readline()
        message = email.message_from_string(message_data)
        messages.append(message)

    return messages
