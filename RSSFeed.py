from django.contrib.syndication.views import Feed
from django.contrib.syndication.views import FeedDoesNotExist
from mailshareapp.models import Mail
from django.template import RequestContext, loader
from mailshareapp import email_utils
from mailshareapp.search import Search


class LatestMailsFeed(Feed):    
    title = "Search Mails"
    link = "http://"
    description = "Updates on changes."
    searchStr=[]
    strRequestURL=''    
  
    def get_object(self, request):       
        self.strRequestURL =  request.META['HTTP_HOST']+request.get_full_path()
	self.strRequestURL=self.strRequestURL.replace("feed/search", "search")
	self.link=self.link + self.strRequestURL
        self.searchStr = Search(request.GET.items())        
        return self.searchStr    

    def items(self):       
        return self.searchStr.get_query_set()

    def item_link(self):	
        return ("http://" + self.strRequestURL)

    def item_title(self, item):
        return item.subject

    def item_description(self, item):
        return item.tags

   


