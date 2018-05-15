
"""
Snippet is a rich snippet that represents a snippet of your mind

Snippet can include url, attachment (thus multimedia). Snippet can also be a frame (if it has children).

For more detail, see  http://.../knowledge_engine/basic_concepts
"""



from brain.config import *
from brain.storage import *


log = getlogger(__name__)


#TODO: es field mapping
#TODO:logger
  

class Snippet:
    """
    Snippet is the most basic data. Based on what fields it has, it can be bookmark/scrap/frame. Based on tags, it can be domain specific data in various apps
    """

    #update_time should always be the currrent time
    #some fields should in get but not in put and post
    fields = ['desc', 'vote', 'private', 'title', 'url', 'tags', 'context', 'attachment', 'init_time', 'update_time']    
    
    def __init__(self, username, id, desc, vote=0, tags=None, private=False, title="", attachment=None, url=None, chilren=None, context=None, init_time=None, update_time=None):         
        """ 
        You are supposed to create and get a snippet only from Mind class instead of instantiate a Snippet instance directly.
        This constructor is used to convert a dict to a Snippet instance
        """        
        self.username = username
        self.id = id        
        if not desc:
            raise Exception('desc is required!')
        self.desc = desc
        self.vote = vote
        self.private = private
        self.title = title
        self.url = url
        self.tags = tags
        self.context = context
        self.attachment = attachment
        self.init_time = init_time
        self.update_time = update_time
        self.in_frames = self.get_in_frames()  
        #search and get annots from es TODO:
        #self.annots = sn_dict.get('annot'
        #TODO: id might be put inside   

    
    def get_storage(self):
        if not hasattr(self, 'storage'):
            self.storage = eval(DEFAULT_STORAGE_CLASS)(self.username)
        return self.storage            


    def get_in_frames(self):
        if hasattr(self, 'id'):
            return self.get_storage().get_in_frames(self.id) 

    @classmethod
    def clean_fields(cls, sn_dict):
        d = {}
        for key, value in sn_dict.items():
            if key in Snippet.fields:
                d[key] = value
        return d         

    def __repr__(self):
        return "<Snippet: %s>" % Snippet.clean_fields(self.__dict__)

    def soft_delete(self):
        pass

    def discard(self):
        self.get_storage().delete_snippet(self.id)

    def save(self):
        """Update the snippet"""
        data_storage_dict = Snippet.clean_fields(self.__dict__.copy())   
        self.get_storage().update_snippet(self.id, data_storage_dict)  

    def add_tags(self, tags):
        pass

    def remove_tags(self, tags):
        pass

    def get_annots(self):
        pass

    def get_comments(self):
        pass

    def is_private(self):
        pass

    def has_attachment(self):
        pass

    def is_img(self):
        pass                    

    #or move to frame?
    def get_children(self):
        pass                

    class DoesNotExist(Exception):
        pass           
            


#support bulk update
class SnippetList:
    pass
 

#TODO:api on group and frame


class Group:
    pass





            
class App:
    """Common interfact that each notebook app need to implement in order to be deployed in the KE platform
    """
    pass


    
    