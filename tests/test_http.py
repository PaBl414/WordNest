"""Run with pytest after installing requirements; uses a temporary database."""
import importlib.util
import os
import tempfile
import unittest

@unittest.skipUnless(importlib.util.find_spec('fastapi') and importlib.util.find_spec('httpx'),'Wymaga fastapi i httpx')
class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        os.environ['WORDNEST_DATA']=cls.temp.name
        from fastapi.testclient import TestClient
        from wordnest.app import app
        cls.client=TestClient(app,base_url='http://127.0.0.1:8000',client=('127.0.0.1',12345))
    @classmethod
    def tearDownClass(cls):cls.client.close();cls.temp.cleanup()
    def test_host_rejected(self):
        self.assertEqual(self.client.get('/api/v1/config',headers={'host':'evil.example'}).status_code,403)
    def test_csrf(self):
        self.assertEqual(self.client.post('/api/v1/sessions',json={}).status_code,403)
    def test_bootstrap_and_session(self):
        c=self.client.get('/api/v1/config').json()
        response=self.client.post('/api/v1/sessions',json={'language':'en','mode':'test','direction':'to_pl'},headers={'Origin':'http://127.0.0.1:8000','X-WordNest-Token':c['token']})
        self.assertEqual(response.status_code,200)
        self.assertNotIn('expected',response.json()['questions'][0])

    def test_set_creation_and_filtered_learning(self):
        config=self.client.get('/api/v1/config').json()
        headers={'Origin':'http://127.0.0.1:8000','X-WordNest-Token':config['token']}
        created=self.client.post('/api/v1/sets',json={'language':'es','name':'Travel'},headers=headers)
        self.assertEqual(created.status_code,200)
        ident=created.json()['id']
        word=self.client.post('/api/v1/words',json={'language':'es','term':'mi conjunto','meaning':'moj zbior','set_id':ident},headers=headers)
        self.assertEqual(word.status_code,200)
        listing=self.client.get('/api/v1/words',params={'language':'es','set_id':ident}).json()
        self.assertEqual(listing['total'],1)
        session=self.client.post('/api/v1/sessions',json={'language':'es','mode':'typing','direction':'to_pl','set_id':ident},headers=headers)
        self.assertEqual(session.status_code,200)
        self.assertEqual([q['prompt'] for q in session.json()['questions']],['mi conjunto'])
        self.assertEqual(self.client.get('/api/v1/words',params={'language':'en','set_id':ident}).status_code,404)

    def test_search_builtin_and_add_to_own_set(self):
        config=self.client.get('/api/v1/config').json()
        headers={'Origin':'http://127.0.0.1:8000','X-WordNest-Token':config['token']}
        group=self.client.post('/api/v1/sets',json={'language':'de','name':'Catalog words'},headers=headers).json()
        url='/api/v1/sets/'+group['id']
        response=self.client.get(url+'/builtin',params={'q':'Mutter'})
        self.assertEqual(response.status_code,200)
        word=next(w for w in response.json()['items'] if 'Mutter' in w['term'])
        self.assertFalse(word['in_set'])
        for _ in range(2):
            self.assertEqual(self.client.post(url+'/words',json={'word_id':word['id']},headers=headers).status_code,200)
        self.assertEqual(self.client.get('/api/v1/words',params={'language':'de','set_id':group['id']}).json()['total'],1)
        self.assertTrue(next(w for w in self.client.get(url+'/builtin',params={'q':'Mutter'}).json()['items'] if w['id']==word['id'])['in_set'])
