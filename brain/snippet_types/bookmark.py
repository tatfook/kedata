
from snippet import Snippet

class BookmarkBook:

    def __init__(self, username):    
        if not username:
            raise Exception('No username given!')    
        self.mind = Mind(username)


    
    def create_bookmark(self, desc, url, vote=0, tags=None, private=False, title="", context=None):
        return Bookmark(self.mind.create_snippet(desc=desc, vote=vote, tags=tags, private=private, title=title, url=url, context=context))

    def get_bookmarks(self):
        self.mind.get_snippets()

    def get_bookmark(self, id):
        return Bookmark(self.mind.get_snippet(id))
             


    class Bookmark:

        def __init__(self, snippet):
            self.snippet = snippet
            self.title = self.snippet.title
            #...


        def save():
            self.snippet.save()    