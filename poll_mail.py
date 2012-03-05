# License: https://github.com/RobFisher/mailshare/blob/master/LICENSE

"""
Poll emails.
"""

# load the Django environment
from django.core.management import setup_environ
import settings
setup_environ(settings)

import mailshareapp.process_emails

mailshareapp.process_emails.poll_emails(True)
