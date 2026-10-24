#!/usr/bin/env python3
"""Starts and stops the frontend (port 8000) and backend (port 8001).

Double-click "Start Weather.command", or run:
    python3 weather/runtime/control.py
"""

import json
import os
import signal
import subprocess
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

APP_ROOT = Path(__file__).resolve().parent.parent
START_PAGE = APP_ROOT / "start.html"
RUNTIME_DIR = Path(__file__).resolve().parent

FRONTEND_PORT = 8000
BACKEND_PORT = 8001
CONTROL_PORT = 8090

SERVICES = {
    "frontend": {"port": FRONTEND_PORT, "script": RUNTIME_DIR / "frontend_server.py"},
    "backend": {"port": BACKEND_PORT, "script": RUNTIME_DIR / "backend_server.py"},
}


def listening_pids(port):
    result = subprocess.run(
        ["lsof", "-nP", "-tiTCP:" + str(port), "-sTCP:LISTEN"],
        capture_output=True,
        text=True,
    )
    pids = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.isdigit():
            pids.append(int(line))
    return pids


def free_port(port):
    own_pid = os.getpid()
    for attempt in range(2):
        pids = [pid for pid in listening_pids(port) if pid != own_pid]
        if not pids:
            return
        sig = signal.SIGTERM if attempt == 0 else signal.SIGKILL
        for pid in pids:
            try:
                os.kill(pid, sig)
            except OSError:
                pass
        for _ in range(25):
            if not [pid for pid in listening_pids(port) if pid != own_pid]:
                return
            time.sleep(0.1)


def service_status():
    return {
        name: {"port": spec["port"], "running": bool(listening_pids(spec["port"]))}
        for name, spec in SERVICES.items()
    }


def start_services(names):
    for name in names:
        spec = SERVICES[name]
        free_port(spec["port"])
        subprocess.Popen(
            [sys.executable, str(spec["script"])],
            cwd=str(APP_ROOT.parent),
            start_new_session=True,
        )

    deadline = time.time() + 5
    pending = set(names)
    while pending and time.time() < deadline:
        pending = {name for name in pending if not listening_pids(SERVICES[name]["port"])}
        if pending:
            time.sleep(0.1)

    status = service_status()
    failed = [name for name in names if not status[name]["running"]]
    return status, failed


def stop_services():
    for spec in SERVICES.values():
        free_port(spec["port"])
    return service_status()


class ControlHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors()
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/start.html"):
            page = START_PAGE.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(page)))
            self.send_cors()
            self.end_headers()
            self.wfile.write(page)
            return
        if path == "/status":
            self.send_json(200, service_status())
            return
        self.send_error(404)

    def do_POST(self):
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw.decode() or "{}")
        except json.JSONDecodeError:
            body = {}

        if path == "/start":
            names = [name for name in ("frontend", "backend") if body.get(name)]
            if not names:
                self.send_json(400, {"error": "Choose frontend, backend, or both."})
                return
            status, failed = start_services(names)
            if failed:
                self.send_json(500, {"error": "Could not start: " + ", ".join(failed) + ".", "status": status})
                return
            self.send_json(200, status)
            return
        if path == "/stop":
            self.send_json(200, stop_services())
            return
        self.send_error(404)

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


def main():
    if listening_pids(CONTROL_PORT):
        if os.environ.get("WEATHER_NO_BROWSER") != "1":
            webbrowser.open("http://127.0.0.1:" + str(CONTROL_PORT) + "/")
        print("Control panel already running: http://127.0.0.1:" + str(CONTROL_PORT) + "/")
        return

    ThreadingHTTPServer.allow_reuse_address = True
    server = ThreadingHTTPServer(("127.0.0.1", CONTROL_PORT), ControlHandler)
    print("Control panel: http://127.0.0.1:" + str(CONTROL_PORT) + "/")

    if os.environ.get("WEATHER_NO_BROWSER") != "1":
        def open_page():
            time.sleep(0.3)
            webbrowser.open("http://127.0.0.1:" + str(CONTROL_PORT) + "/")

        threading.Thread(target=open_page, daemon=True).start()

    server.serve_forever()


if __name__ == "__main__":
    main()
