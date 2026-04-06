import json
import os
import socket
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

from simulator.tracer import Tracer

_server = None
_port = None
_done = False


def _find_free_port():
    with socket.socket() as s:
        s.bind(('', 0))
        return s.getsockname()[1]


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # suppress access logs

    def do_GET(self):
        if self.path == '/':
            self._serve_html()
        elif self.path == '/api/frames':
            self._serve_frames()
        else:
            self._respond(404, 'text/plain', b'Not found')

    def _serve_html(self):
        template = os.path.join(os.path.dirname(__file__), '..', 'visualizer', 'index.html')
        try:
            with open(template) as f:
                html = f.read()
            html = html.replace('const LIVE_MODE = false', 'const LIVE_MODE = true')
            html = html.replace('"__TRACE_DATA__"', 'null')
            self._respond(200, 'text/html', html.encode())
        except Exception as e:
            self._respond(500, 'text/plain', str(e).encode())

    def _serve_frames(self):
        body = json.dumps({"frames": Tracer._frames, "done": _done}).encode()
        self._respond(200, 'application/json', body)

    def _respond(self, code, content_type, body):
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)


def start():
    global _server, _port
    _port = _find_free_port()
    _server = HTTPServer(('localhost', _port), _Handler)
    t = threading.Thread(target=_server.serve_forever, daemon=True)
    t.start()
    return _port


def open_browser(port, delay=1.0):
    def _open():
        time.sleep(delay)
        webbrowser.open('http://localhost:%d' % port)
    threading.Thread(target=_open, daemon=True).start()


def mark_done():
    global _done
    _done = True
