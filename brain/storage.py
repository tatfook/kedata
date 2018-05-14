"""
Storage utility for brain

Currently it supports storage of plain text file on gitlab, with es for search
"""

from datetime import datetime
import gitlab
import yaml
from yaml import CLoader as Loader, CDumper as Dumper
from pytz import timezone
from elasticsearch import Elasticsearch

from brain.config import *



def get_current_year():
    return str(datetime.now().year % 100)


class Storage:

    def create_snippet(self, kwargs):
        pass

    def get_snippet(self, id):
        pass

    def delete_snippet(self, id):
        pass   

    def update_snippet(self, id, kwargs):
        pass     

    def get_snippets(self, q='', tag_name=None, cache_id=None, order_by="init_date"):
        pass  

    def get_in_frames(self, id):             
        pass

    def get_annots(self, id):
        pass             

#TODO:
class DjangoOrmStorage(Storage):
    pass


class GitlabEsStorage(Storage):

    es = Elasticsearch(ES_LOC)
    es_doc_type = 'snippet'

    def __init__(self, username):
        self.username = username
        self._f_dict = {}                
        self._proj = self._get_gitlab_proj()

    #a simple and naive way to get auto increment id. Should be ok since each user's data is stored separately. 
    #For bulk import, just write another api to open and close the file just once.    
    def get_autoincrement_id(self, data_type):
        proj = self._get_gitlab_proj()
        f = proj.files.get(file_path=data_type+'_id_seq', ref='master')    
        current_id = int(f.decode().decode('utf-8'))
        current_id += 1
        f.content = current_id
        f.save(branch='master', commit_message='Update the snippet_id_seq')
        return current_id    

    def get_gitlab_proj_id(self):        
        res_dict = GitlabEsStorage.es.get(index='ke', doc_type='user_data_loc', id=self.username)       
        try:
             if res_dict['found'] == False:
                print('No gitlab project for user ', self.username, ' is found!')
                return 
             else:
                proj_id = res_dict['_source']['proj_id']
                return proj_id
        except IndexError:
            print('No gitlab project for user ', self.username, ' is found!')


    #TODO: support different gitlab urls
    def set_gitlab_proj_id(self, proj_id):        
        GitlabEsStorage.es.index(index='ke', doc_type='user_data_loc', id=self.username, body={'proj_id':str(proj_id)})
        print('Succesfully added user gitlab mapping')


    def _get_gitlab_proj(self):
        if not hasattr(self, '_proj'):
            gl = gitlab.Gitlab(REPO_LOC, private_token=GITLAB_TOKEN)
            proj_id = self.get_gitlab_proj_id()
            try:
                self._proj = gl.projects.get(proj_id) 
                return self._proj   
            except:
                print('Error: failed to get the project!')  
        return self._proj 

       
    
    def get_snippet_id(self):
        return str(self.get_autoincrement_id('snippet'))


    def get_es_index_name(self):
        return 'mind_'+self.username    
        

    @classmethod
    def get_snippet_gitlab_path(cls):
        return 'snippets/'+get_current_year()+'/'
    
    def create_snippet(self, kwargs):
        proj = self._get_gitlab_proj()
        snippet_id = self.get_snippet_id()
        f = proj.files.create({'file_path': GitlabEsStorage.get_snippet_gitlab_path()+snippet_id, #TODO: year
                      'branch': 'master',
                      'content': yaml.dump(kwargs, Dumper=Dumper),
                      'commit_message': 'Created a snippet'})
        print('Succesfully created the snippet!')        
        self._f_dict[snippet_id] =  f
        #get_id() return path like snippets/18/id
        return f.get_id().split('/')[-1]


    def get_snippet(self, id):
        res_dict = GitlabEsStorage.es.get(index=self.get_es_index_name(), doc_type=GitlabEsStorage.es_doc_type, id=str(id))        
        if res_dict['found'] == False:
            print('Snippet ', id, ' not found!')
            return 
        else:
            snippet = res_dict['_source']
            print('snippet found:', snippet)
            return snippet


    def get_in_frames(self, id):             
        payload =  {
                    "query": {
                        "match": {
                          "children": str(id)
                        }
                      }
                   }
        res_dict = GitlabEsStorage.es.search(index=self.get_es_index_name(), doc_type=GitlabEsStorage.es_doc_type, body=payload)       
        if res_dict['hits']['total'] == 0:                                           
            in_frames = None
        else:
            hits = res_dict['hits']['hits']
            in_frames = []
            for hit in hits:
                in_frames.append(hit['_id'])
        return in_frames  


    def get_snippets(self, q='', tag_name=None, cache_id=None, order_by="init_date"):
        #TODO:implement getting notes by cache_id and by q
        if not (q or tag_name or cache_id):                
                res_dict = GitlabEsStorage.es.search(index=self.get_es_index_name(), doc_type=GitlabEsStorage.es_doc_type)                
                if res_dict['hits']['total'] == 0:                                           
                    return []
                else:
                    hits = res_dict['hits']['hits']
                    snippets = []
                    for hit in hits:
                        hit['_source']['id'] = hit['_id']
                        snippets.append(hit['_source'])
                    return snippets   


    def delete_snippet(self, id):
        f = self._get_f(id)
        f.delete(branch='master', commit_message='Delete the snippet')
        print('Snippet ', id, ' succesfully deleted!')


    def update_snippet(self, id, kwargs):
        f = self._get_f(id)
        f.content = yaml.dump(kwargs, Dumper=Dumper)
        f.save(branch='master', commit_message='Update the snippet')        


    def _get_f(self, id):
        if hasattr(self, '_f_dict') and self._f_dict.get(id):
            return self._f_dict.get(id)    
        else:    
            print('file:', GitlabEsStorage.get_snippet_gitlab_path()+str(id))
            f = self._get_gitlab_proj().files.get(file_path=GitlabEsStorage.get_snippet_gitlab_path()+str(id), ref='master')    
            self._f_dict[id] = f
            return f


    @classmethod
    def get_project_username(cls, proj_id):
        payload = {
                  "query": {
                    "match": {
                      "proj_id": str(proj_id)
                    }
                  }
                }
        res_dict = GitlabEsStorage.es.search(index='ke', doc_type='user_data_loc', body=payload)
        return res_dict['hits']['hits'][0]['_id'] 

        
    def gitlab_hook(self, push_event):
        """
        This should be used in a http server to implement the gitlab web hook to be used 
        """
        project_id = push_event.get('project_id', 0)
        print('Event is for project:', project_id)                
        print('username for this project:', self.username)        
        project_url = push_event['project']['http_url']
        commits = push_event['commits']
        proj = self._get_gitlab_proj()
        for commit in commits:
            #TODO:modified and removed
            if commit['added']:
                for item in commit['added']:
                    path = item
                    f = proj.files.get(file_path=path, ref='master')  #TODO:get file of the commit                    
                    content = f.decode().decode("utf-8")  #TODO:
                    id = path.split('/')[-1] #TODO: fet id from the content
                    if path.startswith('snippets/'):
                       res_dict = GitlabEsStorage.es.index(index=self.get_es_index_name(), doc_type=GitlabEsStorage.es_doc_type, id=str(id), body=yaml.load(content))
                       print('hook for add snippet result:', res_dict)
            if commit['modified']:
                for item in commit['modified']:
                    path = item
                    f = proj.files.get(file_path=path, ref='master') 
                    content = f.decode().decode("utf-8")  
                    id = path.split('/')[-1] 
                    if path.startswith('snippets/'):
                        res_dict = GitlabEsStorage.es.index(index=self.get_es_index_name(), doc_type=GitlabEsStorage.es_doc_type, id=str(id), body=yaml.load(content))
                        print('hook for modifying snippet result:', res_dict)
            if commit['removed']:
                for item in commit['removed']:
                    path = item                    
                    if path.startswith('snippets/'):
                        id = path.split('/')[-1] 
                        res_dict = GitlabEsStorage.es.delete(index=self.get_es_index_name(), doc_type=GitlabEsStorage.es_doc_type, id=str(id))
                        print('hook for modifying snippet result:', res_dict)                        
        return project_id
