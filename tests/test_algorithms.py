import json
import random
import subprocess
import sys
import unittest
from algorithms_in_action import run

class AlgorithmsTest(unittest.TestCase):
    def test_sorts_match_python_and_preserve_inputs(self):
        rng = random.Random(8)
        for name in ('insertion-sort', 'merge-sort'):
            for size in range(70):
                values = [rng.randrange(-25, 25) for _ in range(size)]
                original = values[:]
                self.assertEqual(run(name, values).output, sorted(values))
                self.assertEqual(values, original)
    def test_search_first_duplicate_missing_empty(self):
        for name in ('linear-search', 'binary-search'):
            self.assertEqual(run(name, [1, 2, 2, 2, 4], target=2).output, 1)
            self.assertEqual(run(name, [1, 2, 4], target=3).output, -1)
            self.assertEqual(run(name, [], target=3).output, -1)
    def test_binary_requires_sorted_input(self):
        with self.assertRaisesRegex(ValueError, 'ascending'):
            run('binary-search', [2, 1], target=1)
    def test_numeric_validation(self):
        for value in (True, '4', float('nan'), float('inf'), 10**1000):
            with self.assertRaises(ValueError):
                run('merge-sort', [value])
    def test_bfs_cycles_and_destination_only_nodes(self):
        result = run('bfs', graph={'a':['b','c'],'b':['a','d'],'c':['d'],'island':[]}, start='a', end='d')
        self.assertEqual(result.output['path'], ['a','b','d'])
        self.assertIsNone(result.output['distances']['island'])
        self.assertEqual(len(result.output['order']), 4)
        fanout = {'root': ['n'+str(i) for i in range(1000)] * 2}
        self.assertEqual(run('bfs', graph=fanout, start='root', trace_limit=0).metrics['visited'], 1001)
    def test_dijkstra_relaxation_zero_edges_and_disconnection(self):
        graph = {'a':{'b':10,'c':1},'c':{'b':0},'b':{'d':2},'x':{}}
        result = run('dijkstra', graph=graph, start='a', end='d')
        self.assertEqual(result.output['path'], ['a','c','b','d'])
        self.assertEqual(result.output['distances']['d'], 3)
        self.assertIsNone(result.output['distances']['x'])
        self.assertEqual(result.metrics['visited'], 4)
        self.assertIsNone(run('dijkstra', graph=graph, start='a', end='x').output['path'])
        self.assertEqual(run('dijkstra', graph=graph, start='a', end='a').output['path'], ['a'])
    def test_graph_validation(self):
        for graph in ({'a':{'b':-1}}, {'a':{'b':True}}, {'a':['b']}):
            with self.assertRaises(ValueError):
                run('dijkstra', graph=graph, start='a')
        with self.assertRaises(ValueError):
            run('bfs', graph={'a':[]}, start='missing')
        with self.assertRaises(ValueError):
            run('bfs', graph={'a':[]}, start=[])
        with self.assertRaises(ValueError):
            run('linear-search', [1], target=1, trace_limit=True)
    def test_trace_cap_does_not_change_answer(self):
        result = run('insertion-sort', list(range(30,0,-1)), trace_limit=2)
        self.assertTrue(result.trace_truncated)
        self.assertEqual(len(result.steps), 2)
        self.assertEqual(result.output, list(range(1,31)))
    def test_json_cli_and_invalid_input(self):
        good = subprocess.run([sys.executable,'-m','algorithms_in_action','run','binary-search','--values','1,2,2,4','--target','2','--json'], capture_output=True,text=True)
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertEqual(json.loads(good.stdout)['output'], 1)
        bad = subprocess.run([sys.executable,'-m','algorithms_in_action','run','binary-search','--values','2,1','--target','2'],capture_output=True,text=True)
        self.assertEqual(bad.returncode, 2)
        self.assertIn('ascending', bad.stderr)

if __name__ == '__main__':
    unittest.main()
