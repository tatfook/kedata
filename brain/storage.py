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
from elasticsearch.exceptions import NotFoundError as NotFoundInEsError
from elasticsearch_dsl import Search
from unidiff import PatchSet

from brain.config import *

log = getlogger(__name__)


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

    class NotFoundError(Exception):
        pass


#TODO:
class DjangoOrmStorage(Storage):
    pass


#TODO:method to just modify es objects only without affecting gitlab files
class GitlabEsStorage(Storage):

    es = Elasticsearch(ES_LOC)
    es_doc_type = 'snippet'

    def __init__(self, username):
        self.username = username
        self._f_dict = {}     


    
    def get_autoincrement_id(self, data_type):        
        """A simple and naive way to get auto increment id. 

        A plain text file is used to store the seq number for each data type that needs an autoincrement id. 
        It should be ok since each user's data is stored separately. 

        Returns:
            int

        TODO:
            * For bulk import, another api is needed to open and close the file just once
        """
        f = self._get_gitlab_proj().files.get(file_path=data_type+'_id_seq', ref='master')    
        current_id = int(f.decode().decode('utf-8'))
        current_id += 1
        f.content = current_id
        f.save(branch='master', commit_message='Update the snippet_id_seq')
        return current_id    

    def get_gitlab_proj_id(self):        
        res_dict = GitlabEsStorage.es.get(index='ke', doc_type='user_data_loc', id=self.username)       
        try:
             if res_dict['found'] == False:
                log.info('No gitlab project for user %s is found!', self.username)
                return 
             else:
                proj_id = res_dict['_source']['proj_id']
                return proj_id
        except IndexError:
            log.error('No gitlab project for user %s is found!', self.username)


    #TODO: support different gitlab urls
    def set_gitlab_proj_id(self, proj_id):        
        GitlabEsStorage.es.index(index='ke', doc_type='user_data_loc', id=self.username, body={'proj_id':str(proj_id)})
        log.info('Succesfully added user gitlab mapping!')


    def _get_gitlab_proj(self):
        if not hasattr(self, '_proj'):
            gl = gitlab.Gitlab(REPO_LOC, private_token=GITLAB_TOKEN)
            proj_id = self.get_gitlab_proj_id()
            try:
                self._proj = gl.projects.get(proj_id)                   
            except:
                log.error('Error: failed to get the project!')  
            else:
                return self._proj     
        return self._proj 

       
    
    def get_snippet_id(self):
        return self.get_autoincrement_id('snippet')


    def get_es_index_name(self):
        return 'mind_'+self.username    
        

    @classmethod
    def get_snippet_gitlab_path(cls):
        return 'snippets/'+get_current_year()+'/'
    
    def create_snippet(self, **kwargs):   
        """

        """     
        snippet_id = str(self.get_snippet_id())        
        log.info('About to create snippet of id: %s', snippet_id)
        f = self._get_gitlab_proj().files.create({'file_path': GitlabEsStorage.get_snippet_gitlab_path()+snippet_id, #TODO: year
                      'branch': 'master',
                      'content': yaml.dump(kwargs, Dumper=Dumper),
                      'commit_message': 'Created a snippet'})
        log.info('Succesfully created the snippet!')        
        # self._f_dict[snippet_id] =  f
        #get_id() return path like snippets/18/id
        #we want snippet id to be integers #TODO:change other places
        created_snippet_id = int(f.get_id().split('/')[-1])
        log.info('The snippet %s is successfully created!', created_snippet_id)
        return created_snippet_id


    def create_tag(self, **kwargs):        
        name = kwargs.get('name')  
        #check if the tag is already existing     
        try:
            self.get_tag(name)
        except Storage.NotFoundError:    
            pass
        else:    
            #TODO: a new type of Exception
            raise Exception('This tag already exist!')        
        tags_f = self._get_gitlab_proj().files.get(file_path='tags', ref='master')        
        content = tags_f.decode().decode("utf-8")        
        content += '\n\n'+yaml.dump(kwargs, default_flow_style=False, Dumper=Dumper)
        tags_f.content = content
        tags_f.save(branch='master', commit_message='Create a new tag')
        return name       


    def get_snippet(self, id):
        try:
            res_dict = GitlabEsStorage.es.get(index=self.get_es_index_name(), doc_type=GitlabEsStorage.es_doc_type, id=str(id))        
        except NotFoundInEsError:
            raise Storage.NotFoundError('The snippet {} is not found'.format(id))        
        snippet = res_dict['_source']
        log.info('snippet found: %s', snippet)
        return snippet

    def get_tag(self, name):
        log.info('Getting the tag %s...', name)
        try:
            res_dict = GitlabEsStorage.es.get(index=self.get_es_index_name(), doc_type='tag', id=name)
        except NotFoundInEsError:  
            log.info('Tag %s not found', name) 
            raise Storage.NotFoundError('The tag {} is not found'.format(name))          
        tag = res_dict['_source']
        log.info('Tag found: %s', tag)
        return tag
 

    def get_in_frames(self, id):             
        query =  {
                    "query": {
                        "match": {
                          "children": str(id)
                        }
                      }
                   }
        res_dict = GitlabEsStorage.es.search(index=self.get_es_index_name(), doc_type=GitlabEsStorage.es_doc_type, body=query)              
        return [] if  res_dict['hits']['total'] == 0 else  [hit['_id'] for hit in res_dict['hits']['hits']]

   
    def _update(self, sn_dict, id):
        sn_dict.update({'id':id})
        return sn_dict


    def get_snippets(self, q='', tag_name=None, cache_id=None, order_by="init_date"):
        search = Search(using=GitlabEsStorage.es, index=self.get_es_index_name())
        if q:
            search = search.query("match", desc=q)
        if tag_name:
            search = search.query("match", tags=tag_name)    
        r = search.execute()
        return [self._update(hit['_source'], hit['_id']) for hit in r.hits.hits]        

        # if not (q or tag_name or cache_id):    
        #     #TODO:support pagination.             
        #     res_dict = GitlabEsStorage.es.search(index=self.get_es_index_name(), doc_type=GitlabEsStorage.es_doc_type)                                 
        #     return [] if res_dict['hits']['total'] == 0 else [self._update(hit['_source'], hit['_id']) for hit in res_dict['hits']['hits']]  
            #below is the same as be above, but maybe more readable
            # if res_dict['hits']['total'] == 0:                                           
            #     return []
            # else:
            #     hits = res_dict['hits']['hits']
            #     snippets = []
            #     for hit in hits:
            #         hit['_source']['id'] = hit['_id']
            #         snippets.append(hit['_source'])
            #     return snippets

    def get_frames(self, q='', tag_name=None, cache_id=None, order_by="init_date"):
        search = Search(using=GitlabEsStorage.es, index=self.get_es_index_name())
        search = search.filter("exists", field="children")
        if q:
            search = search.query("match", desc=q)
        if tag_name:
            search = search.query("match", tags=tag_name)    
        r = search.execute()
        return [self._update(hit['_source'], hit['_id']) for hit in r.hits.hits]        
        # if not (q or tag_name or cache_id):    
        #     query = {
        #                "query" : {
        #                   "constant_score" : {
        #                      "filter" : {
        #                         "exists" : {
        #                            "field" : "children"
        #                         }
        #                      }
        #                   }
        #                }
        #             }
        #     res_dict = GitlabEsStorage.es.search(index=self.get_es_index_name(), doc_type=GitlabEsStorage.es_doc_type, body=query)  
        #     log.debug('results of searching for frames: %s', res_dict)            
        #     return [] if res_dict['hits']['total'] == 0 else [self._update(hit['_source'], hit['_id']) for hit in res_dict['hits']['hits']] 



    #TODO:search of tags
    def get_tags(self):
        res_dict = GitlabEsStorage.es.search(index=self.get_es_index_name(), doc_type='tag')                
        # if res_dict['hits']['total'] == 0:                                           
        #     return []
        # else:
        #     # hits = res_dict['hits']['hits']
        #     # tags = []
        #     # for hit in hits:                
        #     #     tags.append(hit['_source'])
        #     tags = [hit['_source'] hit for hit in res_dict['hits']['hits']]     
        #     return tags
        return [] if res_dict['hits']['total'] == 0 else [hit['_source'] for hit in res_dict['hits']['hits']]    

    def delete_snippet(self, id):  
        #TODO:removing caching of f
        self._get_f(id).delete(branch='master', commit_message='Delete the snippet')
        log.info('Snippet %s  succesfully deleted!', id)

    def delete_tag(self, name):
        self.get_tag(name)        
        tags_f = self._get_tags_f()
        content = tags_f.decode().decode("utf-8")
        #TODO: yaml multi documents format
        items = content.split('\n\n')        
        items = filter(('\n').__ne__, 
                filter(('').__ne__, items))
        # tags = []
        # for item in items:
        #     tag = yaml.load(item, Loader=Loader)
        #     if tag['name'] != name:
        #         tags.append(tag)
        tags = filter(lambda tag:tag['name'] != name, map(lambda item: yaml.load(item, Loader=Loader), items))        
        # tags_txt_list = []
        # for tag in tags:
        #     tags_txt_list.append(yaml.dump(tag, default_flow_style=False, Dumper=Dumper))            
        # tags_txt = '\n\n'.join(tags_txt_list)        
        tags_txt = '\n\n'.join(list(map(lambda tag:yaml.dump(tag, default_flow_style=False, Dumper=Dumper), tags)))
        #put update of the tag itself into this commit so it is wrapped up like a transaction. 
        actions = [{"action": "update",
                    "file_path": 'tags',
                    "content": tags_txt}
                  ]
        #remove this tag from all snippets that have it
        query= {
                 "query": {
                     "match" : {
                         "tags": name
                     }
                 }
               } 
        res_dict = GitlabEsStorage.es.search(index=self.get_es_index_name(), doc_type=GitlabEsStorage.es_doc_type, body=query) 
        if res_dict['hits']['total'] != 0:                                                   
            hits = res_dict['hits']['hits']               
            snippet_ids = [hit['_id'] for hit in hits]
            log.debug('The following snippets have the tag %s: %s ', name, snippet_ids)
            for snippet_id in snippet_ids:
                f = self._get_f(snippet_id)
                sn = f.decode().decode("utf-8")
                snippet = yaml.load(sn)
                snippet['tags'].remove(name)
                actions.append({"action": "update",
                            "file_path": GitlabEsStorage.get_snippet_gitlab_path()+snippet_id,
                            "content": yaml.dump(snippet, Dumper=Dumper)})

        data = {"branch": "master",
                   "commit_message": "Delete the tag {} and also update snippets that have this tag".format(name) if len(actions) > 1 else "Delete the tag {}. No existing snippets have this tag.".format(name),
                   "actions": actions}  
        self._get_gitlab_proj().commits.create(data)  
        log.info('Tag %s  succesfully deleted!', name)              




    def update_snippet(self, id, kwargs):
        f = self._get_f(id)
        f.content = yaml.dump(kwargs, Dumper=Dumper)
        f.save(branch='master', commit_message='Update the snippet')  


    #TODO:whether to always sort the tag by alphabetic order before writing it back? If so, line number cannot be used to tell which tag has changed. 
    #Currently tags are stored in the order that they are initially written in. 
    def update_tag(self, name, **kwargs):
        log.info('Updating the tag %s with %s', name, kwargs)
        #logic below should be in mind? TODO:        
        #check if there is such a tag
        self.get_tag(name)
        tags_f = self._get_tags_f()        
        content = tags_f.decode().decode("utf-8")        
        items = content.split('\n\n')                
        items = filter(('\n').__ne__, 
                filter(('').__ne__, items))
        new_tag = kwargs
        new_tag['name'] = name                
        tags = list(map(lambda tag: tag if tag['name'] != name else new_tag, map(lambda item: yaml.load(item, Loader=Loader), items)))
        log.debug('tags:%s', tags)
        tags_txt = '\n\n'.join(list(map(lambda tag:yaml.dump(tag, default_flow_style=False, Dumper=Dumper), tags)))
        # put update of the tag itself into this commit so it is wrapped up like a transaction. 
        actions = [{"action": "update",
                    "file_path": 'tags',
                    "content": tags_txt}
                  ]
        #TODO:remove below          
        new_name = kwargs.get('name')
        if new_name and new_name != name:          
            #remove this tag from all snippets that have it
            query= {
                     "query": {
                         "match" : {
                             "tags": name
                         }
                     }
                   } 
            res_dict = GitlabEsStorage.es.search(index=self.get_es_index_name(), doc_type=GitlabEsStorage.es_doc_type, body=query) 
            if res_dict['hits']['total'] == 0:      
                #no snippets have this tag, so just do nothing                                     
                pass
            else:
                hits = res_dict['hits']['hits']
                # snippet_ids = []
                # for hit in hits:
                #     snippet_ids.append(hit['_id'])     
                snippet_ids = [hit['_id'] for hit in hits]
                for snippet_id in snippet_ids:
                    f = self._get_f(snippet_id)
                    sn = f.decode().decode("utf-8")
                    snippet = yaml.load(sn)
                    snippet['tags'] =  list(map(lambda a: a if a!=name else new_name, snippet['tags']))                    
                    actions.append({"action": "update",
                                "file_path": GitlabEsStorage.get_snippet_gitlab_path()+snippet_id,
                                "content": yaml.dump(snippet, Dumper=Dumper)})
            
        data = {"branch": "master",
                   "commit_message": "Updated tags in ses ",
                   "actions": actions}  
        self._get_gitlab_proj().commits.create(data)  
        log.info('Tag %s  succesfully updated!', name)  
        #TODO: parse name from gitlab api return
        return name 


    def update_tag_name(self, name, new_name):        
        """
        The caller should ensure the safety of name and new_name TODO:
        """
        tags_f = self._get_tags_f()
        content = tags_f.decode().decode("utf-8")
        #TODO: do purely file processing?
        items = content.split('\n\n')        
        log.debug('parsed items: %s', items)    
        items = filter(('\n').__ne__, 
                filter(('').__ne__, items))
        #or more readable:
        # items = filter(('').__ne__, items)
        # items = filter(('\n').__ne__, items)
        tags = []
        for item in items:
            tag = yaml.load(item, Loader=Loader)
            if tag['name'] != name:
                tags.append(tag)
            else:
                log.debug('The target tag found, replace its name with the new name...')
                tag['name'] = new_name
                log.debug('The updated tag:%s', tag)
                tags.append(tag)     

        tags_txt_list = []
        for tag in tags:
            tags_txt_list.append(yaml.dump(tag, default_flow_style=False, Dumper=Dumper))
        tags_txt = '\n\n'.join(tags_txt_list)        
        # tags_f.content = tags_txt
        # tags_f.save()
        # put update of the tag itself into this commit so it is wrapped up like a transaction. 
        actions = [{"action": "update",
                    "file_path": 'tags',
                    "content": tags_txt}
                  ]
        
    
        #update this tag from all snippets that have it
        query= {
                 "query": {
                     "match" : {
                         "tags": name
                     }
                 }
               } 
        res_dict = GitlabEsStorage.es.search(index=self.get_es_index_name(), doc_type=GitlabEsStorage.es_doc_type, body=query) 
        if res_dict['hits']['total'] == 0:      
            #no snippets have this tag, so just do nothing                                     
            pass
        else:
            hits = res_dict['hits']['hits']
            snippet_ids = []
            for hit in hits:
                snippet_ids.append(hit['_id'])     

            for snippet_id in snippet_ids:
                f = self._get_f(snippet_id)                
                sn = f.decode().decode("utf-8")
                snippet = yaml.load(sn)
                snippet['tags'] =  list(map(lambda a: a if a!=name else new_name, snippet['tags']))                    
                actions.append({"action": "update",
                            "file_path": GitlabEsStorage.get_snippet_gitlab_path()+snippet_id,
                            "content": yaml.dump(snippet, Dumper=Dumper)})
        
        data = {"branch": "master",
                   "commit_message": "Update the name of the tag {} to {} and also update snippets that have this tag".format(name, new_name) if len(actions) > 1 else 
                                     "Update the name of the tag {} to {}. No existing snippets have this tag.".format(name, new_name),
                   "actions": actions}  
        self._get_gitlab_proj().commits.create(data)  
        log.info('Tag name %s succesfully updated to %s!', name, new_name)   
        #TODO: parse new name from gitlab api return 
        return new_name


    def _get_f(self, id):
        #TODO:remove caching
        # if hasattr(self, '_f_dict') and self._f_dict.get(id):
        #     return self._f_dict.get(id)    
        # else:
            f = self._get_gitlab_proj().files.get(file_path=GitlabEsStorage.get_snippet_gitlab_path()+str(id), ref='master')    
            # self._f_dict[id] = f
            return f

    def _get_tags_f(self):
        #No caching of this anymore. There doesn't seem to be a method to refresh the file
        # if hasattr(self, '_tags_f'):
        #     return self._tags_f
        # else:
            tags_f = self._get_gitlab_proj().files.get(file_path='tags', ref='master')
            # self._tags_f = tags_f
            return tags_f

    @classmethod
    def get_project_username(cls, proj_id):
        query = {
                  "query": {
                    "match": {
                      "proj_id": str(proj_id)
                    }
                  }
                }
        res_dict = GitlabEsStorage.es.search(index='ke', doc_type='user_data_loc', body=query)
        return res_dict['hits']['hits'][0]['_id'] 

        
    def gitlab_hook(self, push_event):
        """
        This should be used in a http server to implement the gitlab web hook to be used 
        """
        project_id = push_event.get('project_id', 0)
        log.info('Received event for project %s', project_id)                
        log.info('Username for this project: %s', self.username)        
        project_url = push_event['project']['http_url']
        commits = push_event['commits']
        proj = self._get_gitlab_proj()
        for commit in commits:            
            if commit['added']:
                for item in commit['added']:
                    path = item
                    f = proj.files.get(file_path=path, ref='master')  #TODO:get file of the commit                    
                    content = f.decode().decode("utf-8")  #TODO:
                    log.debug('Content of the file obtained from gitlab: %s', content)
                    id = path.split('/')[-1] #TODO: fet id from the content
                    if path.startswith('snippets/'):
                       res_dict = GitlabEsStorage.es.index(index=self.get_es_index_name(), doc_type=GitlabEsStorage.es_doc_type, id=str(id), body=yaml.load(content))
                       log.debug('hook for add snippet result: %s', res_dict)                       
            if commit['modified']:
                for item in commit['modified']:
                    path = item
                    f = proj.files.get(file_path=path, ref='master') 
                    content = f.decode().decode("utf-8")  
                    id = path.split('/')[-1] 
                    if path.startswith('snippets/'):
                        res_dict = GitlabEsStorage.es.index(index=self.get_es_index_name(), doc_type=GitlabEsStorage.es_doc_type, id=str(id), body=yaml.load(content))
                        log.debug('hook for modifying snippet result: %s', res_dict)
                    if path == 'tags':
                        #TODO: get the change of tags file in this commit     
                        actual_commit = self._get_gitlab_proj().commits.get(commit['id'])
                        # Get the diff for a commit
                        diff = actual_commit.diff()                                           
                        log.debug('Commit diff: %s', diff)
                        #the actual_commit might have items related to those updated snippets as well since it ask for the commit directly. So we need to get the tags change out
                        # and ignore snippets change from this actual_commit since the info is already in the push event
                        tags_diff = [d for d in diff if d['old_path'] == 'tags'][0]
                        # patch = PatchSet(diff[0]['diff'])
                        patch = PatchSet(tags_diff['diff'])
                        #there shall be only one changed file, which is "tags" file
                        modified_file = patch.modified_files[0]
                        #there shall be only one place of change
                        hunk = modified_file.pop() 
                        added_lines = [line for line in hunk.target_lines() if line.is_added]
                        removed_lines = [line for line in hunk.source_lines() if line.is_removed]
                        log.debug('removed_lines: %s \n added_lines: %s', removed_lines, added_lines)
                        yaml_txt = ''
                        if added_lines and not removed_lines:                            
                            log.info('New tag added!')
                            yaml_txt = '\n'.join([line.value for line in added_lines])
                            log.debug('Content change of tags file: %s', yaml_txt)
                            tag_dict = yaml.load(yaml_txt)
                            tag_name = tag_dict['name']
                            res_dict = GitlabEsStorage.es.index(index=self.get_es_index_name(), doc_type='tag', id=tag_name, body=tag_dict)
                            log.info('A new tag %s is successfully indexed into ES!', tag_name)
                        if added_lines and removed_lines:                            
                            log.info('Tag updated!')
                            #Below's way of trying to re-construct the tag from the diff is really erro prone. For example, some line of 
                            # the previous tag might appear in the context while some line of this tag doesn't appear in the context. Then
                            # the field might get a value of the previous tag. TODO: might change to store each tag a file, which is also easy
                            # for human eyes. Or write a plain text helper utility to get the lines of tag from a line number of change (PatchSet  
                            # provides source_line_no, target_line_no, diff_line_no). Or
                            # just always do operation of tag on the object level instead of file level, and only write the whole tags object into
                            # the file. TODO: 
                            target_context_lines = [line for line in hunk.target_lines() if line.is_context]
                            #TODO:test different cases
                            context_dict = yaml.load('\n'.join([line.value for line in target_context_lines]))
                            #TODO: if tag name gets updated as well
                            tag_name = context_dict.get('name')
                            added_lines_yaml_txt = '\n'.join([line.value for line in added_lines])                        
                            log.debug('Content change of tags file: %s', added_lines_yaml_txt)
                            update_dict = yaml.load(added_lines_yaml_txt)
                            context_dict.update(update_dict)
                            log.info('Tag that is updated is: %s', context_dict)   
                            if not tag_name:
                                log.info('Tag name is changed as well!')                                
                                removed_lines_yaml_txt = '\n'.join([line.value for line in removed_lines])    
                                old_tag_name =  yaml.load(removed_lines_yaml_txt)['name']  
                                new_tag_name = context_dict['name']
                                GitlabEsStorage.es.index(index=self.get_es_index_name(), doc_type='tag', id=new_tag_name, body=context_dict)
                                GitlabEsStorage.es.delete(index=self.get_es_index_name(), doc_type='tag', id=old_tag_name)
                                log.info('The tag name %s is successfully updated to %s in ES!', old_tag_name, new_tag_name) 
                            else:                                                         
                                res_dict = GitlabEsStorage.es.index(index=self.get_es_index_name(), doc_type='tag', id=tag_name, body=context_dict)
                                log.info('The tag %s is successfully updated ES!', tag_name)                            
                        if removed_lines and not added_lines:
                            log.info('Tag removed!')        
                            yaml_txt = '\n'.join([line.value for line in removed_lines])
                            log.debug('Content change of tags file: %s', yaml_txt)
                            tag_dict = yaml.load(yaml_txt)
                            tag_name = tag_dict['name']
                            log.debug('Name of the tag being deleted: %s', tag_name)
                            res_dict = GitlabEsStorage.es.delete(index=self.get_es_index_name(), doc_type='tag', id=tag_name)
                            log.info('The tag %s is successfully removed from ES!', tag_name)
                        
            if commit['removed']:
                for item in commit['removed']:
                    path = item                    
                    if path.startswith('snippets/'):
                        id = path.split('/')[-1] 
                        res_dict = GitlabEsStorage.es.delete(index=self.get_es_index_name(), doc_type=GitlabEsStorage.es_doc_type, id=str(id))
                        log.debug('hook for removing snippet result: %s', res_dict)                        
        return project_id

