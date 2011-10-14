import os
import sys

path = '/srv/www'
if path not in sys.path:
    sys.path.insert(0, path)
mailshare_path = '/srv/www/mailshare'
if mailshare_path not in sys.path:
    sys.path.insert(0, mailshare_path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'mailshare.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

