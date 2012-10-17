from django.contrib.syndication.views import Feed
from django.contrib.syndication.views import FeedDoesNotExist
from mailshareapp.models import Mail
from django.template import RequestContext, loader
from mailshareapp import email_utils
from mailshareapp.search import Search
from mailshareapp.search import get_mail_id_search

class MailsFeed(Feed):    
    title = "Search Mails On Mailshare"
    link = "http://"
    description = "Updates on changes."
    search=[]
    request_url=''
    request_host=''
    title_template='rss/mail_title.html';
    def get_object(self, request):
        self.search = Search(request.GET.items()) 
        self.request_host= request.META['HTTP_HOST']  
        self.request_url =  self.link +self.request_host+self.search.get_url_path()        
        self.link=self.request_url                
        return self.search    

    def items(self):       
        return self.search.get_query_set()

    def item_link(self, item):
        return("http://"+self.request_host+get_mail_id_search(item.id).get_url_path())

    def item_title(self, item):
        return item.subject

    def item_description(self, item):
        return item.tags

   


