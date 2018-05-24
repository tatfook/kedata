#!/usr/bin/env python

import unittest
import time
from brain.mind import Mind
from brain.snippet import Snippet

class TestSnippet(unittest.TestCase):

    def setUp(self):
        self.mind = Mind('leon')
        #TODO:test if able to pass init_time and update_time (so far not supported)
        self.sid = self.mind.create_snippet(desc='Programming language is similar to spoken language', vote=2, tags=['language'], private=False, title="", attachment=None, url="https://git-scm.com/book/en/v7", children=None, context=None)
        self.assertIsInstance(self.sid, int)
        #wait for es to be updated
        time.sleep(6)
    
    def test_get_snippet(self):        
        """
        Testing getting the snippet created in the setup

        This is dependent on whether the webhook configured for the gitlab is running correctly
        """
        print('test_get_snippet:', self.sid)
        s = self.mind.get_snippet(self.sid)
        self.assertEqual(s.vote, 2)
        self.assertEqual(s.desc, 'Programming language is similar to spoken language')
        self.assertFalse(s.private)
        self.assertListEqual(s.tags, ['language'])
        self.assertEqual(s.title, '')
        self.assertIsNone(s.attachment)
        self.assertEqual(s.url, 'https://git-scm.com/book/en/v7')
        # self.assertIsNone(self.context)


    def test_update_snippet(self): 
        print('test_update_snippet:', self.sid)
        s = self.mind.get_snippet(self.sid)
        s.desc = 'Programming language is similar to spoken language!'
        s.vote = 3
        s.private = True
        s.tags = ['language', 'random thought']
        s.title = 'about programming language'
        s.url = 'https://git-scm.com/book/en/v8'
        s.save()
        #wait for es update
        time.sleep(6)
        updated_s = self.mind.get_snippet(self.sid)
        self.assertEqual(updated_s.vote, 3)
        self.assertEqual(updated_s.desc, 'Programming language is similar to spoken language!')
        self.assertTrue(updated_s.private)
        self.assertListEqual(updated_s.tags, ['language', 'random thought'])
        self.assertEqual(updated_s.title, 'about programming language')
        self.assertIsNone(updated_s.attachment)
        self.assertEqual(updated_s.url, 'https://git-scm.com/book/en/v8')
        

    def test_get_snippets(self):
        sns = self.mind.get_snippets()
        sids = [s.id for s in sns]
        self.assertIn(str(self.sid), sids)



    def test_in_frames(self):
        fid = self.mind.create_snippet(desc='parent of the testing snippet', vote=2, tags=['language'], private=False, title="parent", attachment=None, url="https://git-scm.com/book/en/v7", children=[self.sid], context=None)
        print('frame id:', fid)
        time.sleep(6)
        frame = self.mind.get_snippet(fid)
        s = self.mind.get_snippet(self.sid)
        print('The snippet is in frames:', s.in_frames)
        self.assertIn(str(fid), s.in_frames)



    def tearDown(self):
        print('tear down:', self.sid)
        s = self.mind.get_snippet(self.sid)
        s.discard()
        #wait for es to get updated
        time.sleep(6)        
        self.assertRaises(Snippet.DoesNotExist, self.mind.get_snippet, self.sid)

    



if __name__ == "__main__":
    unittest.main()        