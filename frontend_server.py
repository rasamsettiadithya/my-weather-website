#!/usr/bin/env python3
"""Frontend runtime. Serves the weather page only. Port 8000."""

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = 8000
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


class FrontendHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)


if __name__ == "__main__":
    ThreadingHTTPServer.allow_reuse_address = True
    server = ThreadingHTTPServer(("127.0.0.1", PORT), FrontendHandler)
    print("Frontend: http://127.0.0.1:" + str(PORT) + "/weather.html")
    server.serve_forever()
