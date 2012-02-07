# License: https://github.com/RobFisher/mailshare/blob/master/LICENSE

"""Utility to fix dates on emails in the event that a user decides
to forward their entire sent items folder to Mailshare."""

# load the Django environment
from django.core.management import setup_environ
import settings
setup_environ(settings)

from mailshareapp.models import Mail, Contact
import datetime
from django.utils.html import strip_tags

def fix_dates(contact_id):
    contact = Contact.objects.get(id=contact_id)
    mails_from_contact = Mail.objects.filter(sender__id=contact_id)
    for m in mails_from_contact:
        # only process forwarded emails
        subject = m.subject.lower()
        if subject[0:2] == 'fw':
            body = strip_tags(m.body)
            firstFromIndex = body.find('From:')
            firstSentIndex = body.find('Sent:')
            firstToIndex = body.find('To:')
            fromString = body[firstFromIndex+6:firstSentIndex].strip()
            sentString = body[firstSentIndex+6:firstToIndex].strip()
            if fromString == contact.name:
                try:
                    dt = datetime.datetime.strptime(sentString, '%d %B %Y %H:%M')
                except:
                    print 'Unrecognised date ' + sentString + ' in mail ' + str(m.id)
                else:
                    m.date = dt
                    m.save()
                    print str(m.id) + ' ok ' + str(dt)
            else:
                print 'Wrong sender ' + fromString + ' in mail ' + str(m.id)


import sys

if __name__ == '__main__':
    contact_id = int(sys.argv[1])
    fix_dates(contact_id)
