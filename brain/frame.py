

from brain.config import *
from brain.storage import *

class Frame(Snippet):

    primary_key = 'id'
    fields = ('desc', 'vote', 'private', 'title', 'tags', 'attachment', 'init_time', 'update_time')
       

    
    def add_children(self):
        pass

    def get_related_frames(self):
        pass


    def get_parents(self):
        pass    

    def save(self):
        pass

    def destroy(self):
        pass
            