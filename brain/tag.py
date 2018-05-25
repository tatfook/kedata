

# from brain.base import *
from brain.config import *
from brain.storage import *

#TODO: don't allow changing of name (field that behave like primary key in database) after __init__()
class Tag(object):

    # __metaclass__ = Data

    primary_key = 'name'

    fields = ('name', 'desc', 'private','init_time', 'update_time')

    def __init__(self, username, name, desc='', private=False, init_time=None, update_time=None):    
        if not username:
            raise Exception('No username given!')    
        self.username = username
        self.name = name
        self.desc = desc
        self.private = private
        self.init_time = init_time
        self.update_time = update_time


    #TODO:change sn_dict to **kwargs
    @classmethod
    def clean_fields(cls, sn_dict):
        d = {}
        for key, value in sn_dict.items():
            if key in cls.fields:
                d[key] = value
        return d 

    def get_related_tags(self):
        pass

    @classmethod
    def merge(tag1, tag2, new_tag_name):
        pass    
    

    def discard(self):
        self.get_storage().delete_tag(self.name)

    def save(self):
        """Update the tag"""
        data_storage_dict = Tag.clean_fields(self.__dict__.copy())   
        try:
            self.get_storage().update_tag(**data_storage_dict)      
        except Storage.NotFoundError:
            #TODO: new type of Exception
            raise Tag.DoesNotExist('If you want to update tag name, please use Mind class to do so!')
               
   


    #TODO:refactor
    def get_storage(self):
        if not hasattr(self, 'storage'):
            self.storage = eval(DEFAULT_STORAGE_CLASS)(self.username)
        return self.storage       


    class DoesNotExist(Exception):
        pass  