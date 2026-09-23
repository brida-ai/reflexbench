import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from systemone_http import SystemOneHttpClient, SystemOneHttpError


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def do_POST(self):
        n = int(self.headers.get("content-length", "0"))
        body = json.loads(self.rfile.read(n))
        if body.get("model") == "fail":
            raw = b'{"error":"bad"}'
            self.send_response(422)
        else:
            raw = json.dumps({"answers": {"q": {"type": "noul", "noul": 0.8}}}).encode()
            self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)
    def log_message(self, *_):
        pass


class SystemOneHttpTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join(timeout=2)

    def test_reuses_client_and_parses_response(self):
        with SystemOneHttpClient(self.url) as client:
            one = client.request("x", {"q": {"type": "noul", "instructions": "?"}})
            two = client.request("y", {"q": {"type": "noul", "instructions": "?"}})
        self.assertEqual(one.status, 200)
        self.assertEqual(one.payload["answers"]["q"]["noul"], 0.8)
        self.assertGreaterEqual(two.latency_ms, 0)

    def test_http_failure_is_explicit(self):
        with SystemOneHttpClient(self.url) as client:
            with self.assertRaises(SystemOneHttpError) as ctx:
                client.request("x", {"q": {"type": "noul"}}, model="fail")
        self.assertEqual(ctx.exception.status, 422)


if __name__ == "__main__":
    unittest.main()
