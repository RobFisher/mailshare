# License: https://github.com/RobFisher/mailshare/blob/master/LICENSE

from django.db import models

class Contact(models.Model):
    name = models.TextField()
    address = models.TextField()
    def __unicode__(self):
        return self.address

class Mail(models.Model):
    sender = models.ForeignKey(Contact, related_name='sent_mails')
    to = models.ManyToManyField(Contact, related_name='received_mails')
    cc = models.ManyToManyField(Contact, related_name='cced_mails')
    subject = models.TextField(default='')
    date = models.DateTimeField(default='')
    message_id = models.TextField(default='')
    thread_index = models.TextField(default='')
    in_reply_to = models.TextField(default='')
    references = models.TextField(default='')
    content_type = models.TextField(default='')
    body = models.TextField(default='')
    def __unicode__(self):
        return self.date.isoformat() + ' ' + self.sender.address[0:20] + ' ' + self.subject[0:30]
    class Meta:
        ordering = ['-date']
