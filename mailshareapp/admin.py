from mailshareapp.models import Mail, Contact
from django.contrib import admin

class MailAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Contacts', {'fields': ['sender', 'to', 'cc']}),
        ('Details', {'fields': ['subject', 'date']}),
        ('Indexing', {'fields': ['message_id', 'thread_index'], 'classes': ['collapse']}),
        (None, {'fields': ['body']}),
    ]
    list_display = ('sender', 'date', 'subject')
    list_display_links = ['date']
    list_filter = ['date']
    date_hierarchy = 'date'
    search_fields = ['subject', 'body']

admin.site.register(Mail, MailAdmin)
admin.site.register(Contact)
