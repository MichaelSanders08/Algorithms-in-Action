"""A bounded, loopback-only learning lab using the actual Python algorithms."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from .core import ALGORITHMS, run

ASSETS = Path(__file__).with_name('web_assets')


def compute(payload):
    if not isinstance(payload, dict):
        raise ValueError('Send an object containing an algorithm and its inputs.')
    name = payload.get('algorithm')
    if not isinstance(name, str) or name not in ALGORITHMS:
        raise ValueError('Choose one of the six algorithms.')
    if ALGORITHMS[name]['kind'] == 'graph':
        graph = payload.get('graph')
        if not isinstance(graph, dict) or not graph or len(graph) > 24:
            raise ValueError('The visual lab supports 1–24 graph nodes. Use the CLI for larger graphs.')
        nodes = set(graph)
        edges = 0
        for node, neighbors in graph.items():
            if not isinstance(node, str) or not 1 <= len(node) <= 40 or not isinstance(neighbors, (dict, list)):
                raise ValueError('Use short node names and adjacency arrays (BFS) or weight objects (Dijkstra).')
            for neighbor in neighbors:
                if not isinstance(neighbor, str) or not 1 <= len(neighbor) <= 40:
                    raise ValueError('Neighbor names must contain 1–40 characters.')
                nodes.add(neighbor)
            edges += len(neighbors)
        if len(nodes) > 24 or edges > 120:
            raise ValueError('The visual lab supports up to 24 total nodes and 120 edges.')
        result = run(name, graph=graph, start=payload.get('start'), end=payload.get('end') or None, trace_limit=500)
    else:
        values = payload.get('values')
        if not isinstance(values, list) or len(values) > 80:
            raise ValueError('The visual lab supports up to 80 values. Use the CLI for larger inputs.')
        result = run(name, values, target=payload.get('target'), trace_limit=500)
    return result.to_dict()


class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def allowed(self):
        expected = f'127.0.0.1:{self.server.server_port}'
        return self.headers.get('Host') == expected and self.headers.get('Origin', 'http://'+expected) == 'http://'+expected

    def reply(self, code, body, mime='application/json'):
        content = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        if not self.allowed():
            return self.reply(403, '{"error":"Use the printed loopback address."}')
        path = urlsplit(self.path).path
        if path == '/favicon.ico':
            return self.reply(204, b'', 'image/x-icon')
        if path == '/api/algorithms':
            return self.reply(200, json.dumps(ALGORITHMS))
        files = {'/': ('index.html', 'text/html; charset=utf-8'), '/lab.js': ('lab.js', 'text/javascript; charset=utf-8'), '/lab.css': ('lab.css', 'text/css; charset=utf-8')}
        if path not in files:
            return self.reply(404, '{"error":"Not found."}')
        filename, mime = files[path]
        return self.reply(200, (ASSETS/filename).read_bytes(), mime)

    def do_POST(self):
        if not self.allowed():
            return self.reply(403, '{"error":"Cross-origin requests are not allowed."}')
        if self.path != '/api/run':
            return self.reply(404, '{"error":"Not found."}')
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 64000 or self.headers.get_content_type() != 'application/json':
                raise ValueError('Send JSON under 64 KB.')
            result = compute(json.loads(self.rfile.read(size)))
            self.reply(200, json.dumps(result, allow_nan=False))
        except (ValueError, TypeError, OverflowError, RecursionError):
            # Keep validation useful without exposing paths or request contents.
            self.reply(400, json.dumps({'error': 'Invalid inputs. Use finite numbers, ascending values for binary search, and valid graph nodes/nonnegative weights. Lab limits: 80 values, 24 nodes, 120 edges.'}))

    def log_message(self, *_args):
        pass


def serve(port=4176):
    if type(port) is not int or not 1024 <= port <= 65535:
        raise ValueError('Choose a port from 1024 to 65535.')
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    print(f'Algorithms learning lab: http://127.0.0.1:{port}/\nPress Ctrl+C to stop. Inputs stay on this computer.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
