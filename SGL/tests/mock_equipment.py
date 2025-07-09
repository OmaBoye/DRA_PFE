# tests/mock_equipment.py
from http.server import BaseHTTPRequestHandler, HTTPServer

class MockEquipmentServer(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"status":"received"}')

def run_mock_server():
    server = HTTPServer(('localhost', 8001), MockEquipmentServer)
    server.serve_forever()