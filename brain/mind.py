#!/usr/bin/env python

from pytz import timezone
from datetime import datetime

from brain.snippet import *
from brain.storage import *


class Mind:
    """
    Mind can be stored on any kind of substance. More type of storage will be supported, for example gitlab hosted project files with search provided with es, 
    or local plain text files managed, with git with searching provided with sqlite, and etc.   
    """

    def __init__(self, username):    
        if not username:
            raise Exception('No username given!')    
        self.username = username
              
        self.storage = GitlabEsStorage(username) 

    # def get_note_cls(self, bookname='snippet'):   
    #     try:     
    #         return getNote(self.username, bookname)       
    #     except:
    #         raise Exception('Invalid username!')     

    
    def create_snippet(self, **kwargs):                         
        now = timezone(TIME_ZONE).localize(datetime.now()).replace(microsecond=0).isoformat()            
        #TODO: consider case of bulk importing, which probably already have init_time and update_time
        kwargs = Snippet.clean_fields(kwargs)
        # if not kwargs.get('init_time'):    
        kwargs['init_time'] = now
        # if not kwargs.get('update_time'):
        kwargs['update_time'] = now   
        id = self.storage.create_snippet(kwargs)        
        s = Snippet(self.username, id, **kwargs)        
        s.storage = self.storage
        return s
    
    def get_snippet(self, id): 
        """
        Can get a frame as well
        """       
        kwargs = self.storage.get_snippet(id)        
        if not kwargs:
            raise Snippet.DoesNotExist  
        s = Snippet(self.username, id, **kwargs)        
        s.storage = self.storage
        return s
    
    
    #TODO: use GitlabEsStorage as well
    def get_snippets(self, q='', tag_name=None, cache_id=None, order_by="init_date"):
        """
        Can get frames as well
        """
        sns = self.storage.get_snippets(q='', tag_name=None, cache_id=None, order_by="init_date")                            
        snippets = []
        for sn in sns:
            snippets.append(Snippet(self.username, **sn))
        return snippets    
        # return SnippetList(snippets)
  

    @classmethod
    def display_snippets(cls, snippet, template="snippet.html", style="snippet_default.css"):
        pass


    def create_tag(self, kwargs):
        pass

    def get_tag(self, tag_name):
        pass

    def get_tags(self, tag_name):
        pass    

    def merge_tag(self, tag_name1, tag_name2, new_tag_name):
        pass





if __name__ == '__main__':
    mind = Mind('leon')
    s1 = mind.get_snippet(5)
    print('s1:', s1)       
    s2 = mind.create_snippet(desc='Programming language is similar to spoken language', vote=2, tags=['language'], private=False, title="", attachment=None, url="https://git-scm.com/book/en/v7", chilren=None, context=None)
    print('s2:', s2)
    s2.desc = 'Programming language is similar to spoken language!'
    s2.save()  
    #wait for es to be updated
    import time
    time.sleep(6)
    s3 = mind.get_snippet(s2.id)
    print('s3:', s3)  
    snippets = mind.get_snippets()
    print('snippets:', snippets)        