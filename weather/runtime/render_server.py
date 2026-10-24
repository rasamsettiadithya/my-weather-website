#!/usr/bin/env python3
"""Render runtime. Serves the weather page and /weather on one port."""

import json
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

APP_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_ROOT))

from backend.weather_service import weather_report

FRONTEND_DIR = APP_ROOT / "frontend"
PORT = int(os.environ.get("PORT", "8000"))


class RenderHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            self.send_response(302)
            self.send_header("Location", "/weather.html")
            self.end_headers()
            return
        if parsed.path == "/weather":
            query = parse_qs(parsed.query)
            raw_cities = query.get("cities", [""])[0]
            city_ids = [city_id.strip() for city_id in raw_cities.split(",") if city_id.strip()]
            self.reply(city_ids)
            return
        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/weather":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw.decode() or "{}")
        except json.JSONDecodeError:
            self.send_json(400, {"error": "Payload must be JSON."})
            return

        cities = body.get("cities", [])
        if not isinstance(cities, list):
            self.send_json(400, {"error": "cities must be a list of city names."})
            return
        city_ids = [str(city_id).strip() for city_id in cities if str(city_id).strip()]
        self.reply(city_ids)

    def reply(self, city_ids):
        try:
            self.send_json(200, weather_report(city_ids))
        except ValueError as error:
            self.send_json(400, {"error": str(error)})
        except Exception:
            self.send_json(502, {"error": "Weather could not be loaded."})

    def send_json(self, status, body):
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_cors()
        self.end_headers()
        self.wfile.write(payload)

    def send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


if __name__ == "__main__":
    ThreadingHTTPServer.allow_reuse_address = True
    server = ThreadingHTTPServer(("0.0.0.0", PORT), RenderHandler)
    print("Render app: http://0.0.0.0:" + str(PORT) + "/")
    server.serve_forever()
