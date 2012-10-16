from django.conf.urls.defaults import *
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from dajaxice.core import dajaxice_autodiscover
dajaxice_autodiscover()
from RSSFeed import LatestMailsFeed

urlpatterns = patterns('mailshareapp.views',
    (r'^$', 'index_view'),
    (r'^search/$', 'search_view'),
    (r'^advanced/$', 'advanced_view'),
    (r'^teams/$', 'teams_view'),
    (r'feed/search/$', LatestMailsFeed()),
    #(r'^browse/$', 'browse'),
    #(r'^view/(?P<email_id>\d+)/$', 'email'),
)

urlpatterns += patterns('',
    # Example:
    # (r'^mailshare/', include('mailshare.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    (r'^%s/' % settings.DAJAXICE_MEDIA_PREFIX, include('dajaxice.urls')),
)
