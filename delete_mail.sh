#!/bin/bash
mysql -u root -p << eof
USE mailshare;
DROP TABLE mailshareapp_mail;
DROP TABLE mailshareapp_mail_to;
DROP TABLE mailshareapp_mail_cc;
DROP TABLE mailshareapp_mail_tags;
eof
python manage.py syncdb

