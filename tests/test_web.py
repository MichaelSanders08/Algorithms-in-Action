import json
import unittest
from algorithms_in_action.web import compute, ASSETS
from algorithms_in_action.core import run

class LabTests(unittest.TestCase):
    def test_same_algorithms_and_duplicate_search(self):
        values=[1,3,3,7]
        actual=compute({'algorithm':'binary-search','values':values,'target':3})
        self.assertEqual(actual,run('binary-search',values,target=3,trace_limit=500).to_dict())
        self.assertEqual(actual['output'],1)
        self.assertEqual(values,[1,3,3,7])

    def test_both_graph_formats_and_unreachable_destination(self):
        bfs=compute({'algorithm':'bfs','graph':{'a':['b'],'b':[],'c':[]},'start':'a','end':'c'})
        self.assertIsNone(bfs['output']['path'])
        weighted=compute({'algorithm':'dijkstra','graph':{'a':{'b':0},'b':{'c':2},'c':{}},'start':'a','end':'c'})
        self.assertEqual(weighted['output']['path'],['a','b','c'])
        self.assertEqual(weighted['output']['distances']['c'],2)

    def test_lab_limits_include_implicit_graph_nodes(self):
        for payload in ({'algorithm':'insertion-sort','values':[1]*81},{'algorithm':'bfs','graph':{'a':[str(i) for i in range(25)]},'start':'a'},{'algorithm':'binary-search','values':[3,1],'target':1},{'algorithm':'dijkstra','graph':{'a':{'b':-1}},'start':'a'}):
            with self.subTest(payload=str(payload)[:60]), self.assertRaises(ValueError):compute(payload)

    def test_packaged_browser_assets_exist(self):
        for file in ('index.html','lab.js','lab.css'):
            self.assertTrue((ASSETS/file).is_file())

class LabHTTPTests(unittest.TestCase):
    def test_loopback_api_and_asset_boundaries(self):
        import http.client
        import threading
        from http.server import ThreadingHTTPServer
        from algorithms_in_action.web import Handler
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
        try:
            conn=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=5)
            conn.request('GET','/');response=conn.getresponse();self.assertEqual(response.status,200);self.assertIn(b'Learning lab',response.read())
            conn.request('POST','/api/run',json.dumps({'algorithm':'merge-sort','values':[3,-1,2]}),{'Content-Type':'application/json'});response=conn.getresponse();self.assertEqual(response.status,200);self.assertEqual(json.loads(response.read())['output'],[-1,2,3])
            conn.request('POST','/api/run','{}',{'Content-Type':'application/json','Origin':'https://foreign.example'});response=conn.getresponse();self.assertEqual(response.status,403);response.read()
            conn.request('GET','/../../pyproject.toml');response=conn.getresponse();self.assertEqual(response.status,404);response.read()
            conn.close()
        finally:
            server.shutdown();server.server_close();worker.join()
