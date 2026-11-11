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
