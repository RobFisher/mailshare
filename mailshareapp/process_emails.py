# License: https://github.com/RobFisher/mailshare/blob/master/LICENSE

import poll_imap_email

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


def print_message_headers(message):
    """Given an email.message.Message object, print out some interesting headers."""
    print "To: " + message.get('To')
    print "From: " + message.get('From')
    print "Subject: " + message.get('Subject')
    print "Date: " + message.get('Date')

if __name__ == '__main__':
    messages = poll_imap_email.fetch_messages()
    for message in messages:
        print_message_headers(message)
        plain_body = get_plain_body(message)
        print("-----")
        print(plain_body)
        print("-----")
        print("")
