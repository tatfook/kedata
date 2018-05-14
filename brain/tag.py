
class Tag:
    pass


    def __init__(self, username):    
        if not username:
            raise Exception('No username given!')    
        self.username = username


    def get_related_tags(self):
        pass

    @classmethod
    def merge(tag1, tag2, new_tag_name):
        pass    

    def destroy(self):
        pass
