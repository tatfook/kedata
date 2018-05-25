

from brain.config import *
from brain.storage import *
from brain.snippet import Snippet

class Frame(Snippet):

    primary_key = 'id'
    fields = ('desc', 'vote', 'private', 'title', 'tags', 'attachment', 'children','init_time', 'update_time')
       
    
    def add_children(self):
        pass

    def remove_children(self):
        pass    

    def get_related_frames(self):
        pass


    def get_parents(self):
        pass    

    def save_children_order(self):
        pass

    def destroy(self):
        pass
            