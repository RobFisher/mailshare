# License: https://github.com/RobFisher/mailshare/blob/master/LICENSE

from mailshare.mailshareapp.models import Mail, Tag

def add_autotags_to_mail(m):
    """Search the mail body for each autotag and add it if found"""
    # TODO - maybe it would be quicker or better to make a queryset out of the
    # email and use a common function for adding tags to new emails and new
    # tags to existing emails
    tags = Tag.objects.filter(auto=True)
    for t in tags:
        tag_lowercase = t.name.lower()
        if m.subject.lower().find(tag_lowercase) != -1:
            m.tags.add(t)
        # TODO: find out why this gives UnicodeDecodeError: 'ascii' codec can't decode
        # Where is the ascii here?
        #elif m.body.lower().find(tag_lowercase) != -1:
        else:
            try:
                found = m.body.lower().find(tag_lowercase)
            except UnicodeDecodeError:
                pass
            else:
                if found != -1:
                    m.tags.add(t)
