#!/usr/bin/env python

import unittest
import time
import random
from brain.mind import Mind
from brain.tag import Tag


class TestTag(unittest.TestCase):

    def setUp(self):
        self.mind = Mind('leon')
        #cleaning up testing tags first
        self.mind.remove_testing_tags()
        #TODO:test if able to pass init_time and update_time (so far not supported)
        self.tag_name = self.mind.create_tag(name='tagfortesting'+str(random.randint(0, 10000)), desc='a random tag for testing', private=False)  
        print('Created tag:', self.tag_name)      
        #wait for es to be updated
        time.sleep(6)
    
    def test_get_tag(self):        
        """
        Testing getting the tag created in the setup

        This is dependent on whether the webhook configured for the gitlab is running correctly
        """
        print('test_get_tag:', self.tag_name)
        t = self.mind.get_tag(self.tag_name)
        self.assertEqual(t.name, self.tag_name)
        self.assertEqual(t.desc, 'a random tag for testing')
        self.assertFalse(t.private)        
        

    def test_update_tag(self): 
        print('test_update_tag:', self.tag_name)
        t = self.mind.get_tag(self.tag_name)
        t.desc = 'Tagging is ok!'        
        t.private = True        
        t.save()
        #wait for es update
        time.sleep(6)
        updated_t = self.mind.get_tag(self.tag_name)        
        self.assertEqual(updated_t.desc, 'Tagging is ok!')
        self.assertTrue(updated_t.private)    


    def test_update_tag_with_name(self):
        """Update the tag name together with the content
        """        
        print('test_update_tag_with_name:', self.tag_name)
        t = self.mind.get_tag(self.tag_name)
        new_name = 'tagfortesting'+str(random.randint(0, 10000))
        t.name = new_name
        t.desc = 'Tagging is ok!'        
        t.private = True                
        self.assertRaises(Tag.DoesNotExist, t.save)   



    def test_get_tags(self):        
        tags = self.mind.get_tags()
        print('Tags of %s: %s' % (self.mind.username, [tag.name for tag in tags]))        
        

        

    def test_update_tag_name(self):        
        new_name = 'tagfortesting'+str(random.randint(0, 10000))
        old_name = self.tag_name
        print('Updating the tag %s to the new name %s' % (old_name, new_name))
        self.tag_name = self.mind.update_tag_name(self.tag_name, new_name)
        time.sleep(6)
        self.assertEqual(self.tag_name, new_name)
        t = self.mind.get_tag(new_name)
        self.assertEqual(t.name, new_name)
        self.assertRaises(Tag.DoesNotExist, self.mind.get_tag, old_name)

        
    def test_update_tag_with_snippets(self):
        """Testing if sniippets having the tag get changed after tag name changing
        """
        old_name = 'testingsnippetchangeaftertagnamechange'
        new_name = 'testingsnippetchangeaftertagnamechanged'
        self.mind.create_tag(name=old_name, desc='a random tag for testing', private=True)  
        time.sleep(6)
        t = self.mind.get_tag(old_name)
        self.assertEqual(t.name, old_name)
        sid1 = self.mind.create_snippet(desc='Snippet 1 for testing snippets change with tag name change', vote=-1, tags=[old_name], private=True, title="", attachment=None, url=None, chilren=None, context=None)    
        time.sleep(6)
        s1 = self.mind.get_snippet(sid1)
        self.assertEqual(s1.desc, 'Snippet 1 for testing snippets change with tag name change')
        print('s1.tags:', s1.tags)
        self.assertListEqual(s1.tags, [old_name])
        sid2 = self.mind.create_snippet(desc='Snippet 2 for testing snippets change with tag name change', vote=-1, tags=[old_name], private=True, title="", attachment=None, url=None, chilren=None, context=None)    
        time.sleep(6)
        s2 = self.mind.get_snippet(sid2)
        print('s2.tags:', s2.tags)
        self.assertEqual(s2.desc, 'Snippet 2 for testing snippets change with tag name change')
        self.assertListEqual(s2.tags, [old_name])
        self.mind.update_tag_name(old_name, new_name)
        time.sleep(6)
        self.assertRaises(Tag.DoesNotExist, self.mind.get_tag, old_name)
        t = self.mind.get_tag(new_name)
        self.assertEqual(t.name, new_name)
        s1_new = self.mind.get_snippet(sid1)
        print('s1_new.tags:', s1_new.tags)
        self.assertListEqual(s1_new.tags, [new_name])
        s2_new = self.mind.get_snippet(sid2)
        print('s2_new.tags:', s2_new.tags)
        self.assertListEqual(s2_new.tags, [new_name])


    def test_delete_tag_with_snippets(self):
        """Testing if sniippets having the tag get changed after tag deletion 
        """
        tag_name = 'testingsnippetchangeaftertagnamedelete'        
        self.mind.create_tag(name=tag_name, desc='a random tag for testing', private=True)  
        time.sleep(6)
        t = self.mind.get_tag(tag_name)
        self.assertEqual(t.name, tag_name)
        sid1 = self.mind.create_snippet(desc='Snippet 1 for testing snippets change with tag deletion', vote=-1, tags=[tag_name], private=True, title="", attachment=None, url=None, chilren=None, context=None)    
        time.sleep(6)
        s1 = self.mind.get_snippet(sid1)
        print('s1.tags:', s1.tags)
        self.assertEqual(s1.desc, 'Snippet 1 for testing snippets change with tag deletion')
        self.assertListEqual(s1.tags, [tag_name])
        sid2 = self.mind.create_snippet(desc='Snippet 2 for testing snippets change with tag deletion', vote=-1, tags=[tag_name], private=True, title="", attachment=None, url=None, chilren=None, context=None)    
        time.sleep(6)
        s2 = self.mind.get_snippet(sid2)
        print('s2.tags:', s2.tags)
        self.assertEqual(s2.desc, 'Snippet 2 for testing snippets change with tag deletion')
        self.assertListEqual(s2.tags, [tag_name])
        t.discard()
        time.sleep(6)
        self.assertRaises(Tag.DoesNotExist, self.mind.get_tag, tag_name)
        s1_new = self.mind.get_snippet(sid1)
        print('s1_new.tags:', s1_new.tags)
        self.assertListEqual(s1_new.tags, [])
        s2_new = self.mind.get_snippet(sid2)
        print('s2_new.tags:', s2_new.tags)
        self.assertListEqual(s2_new.tags, [])        

    

    def tearDown(self):
        print('tear down:', self.tag_name)
        t = self.mind.get_tag(self.tag_name)
        t.discard()
        #wait for es to get updated
        time.sleep(6)        
        self.assertRaises(Tag.DoesNotExist, self.mind.get_tag, self.tag_name)
        # self.mind.remove_testing_tags()

    



if __name__ == "__main__":
    unittest.main()        