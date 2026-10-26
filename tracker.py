"""Run the local Fritlas dashboard and optionally collect foreground-window changes on Windows."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import analysis
from activity import ActivityTracker
from paths import RESOURCE_ROOT
import storage

STATIC = RESOURCE_ROOT / "web"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC), **kwargs)

    def do_GET(self):
        if self.path == "/api/summary":
            events = [dict(row) for row in storage.recent_events(limit=None)]
            payload = json.dumps({
                "summary": analysis.summarize(events),
                "events": events,
                "feedback": [dict(row) for row in storage.recent_feedback()],
                "check_in": dict(storage.latest_check_in()) if storage.latest_check_in() else None,
            }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        return super().do_GET()

    def do_POST(self):
        if self.path != "/api/check-in":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length))
            intention = str(body.get("intention", "")).strip()[:240]
            energy = max(1, min(5, int(body.get("energy", 3))))
            if not intention:
                raise ValueError("An intention is required.")
            storage.add_check_in(datetime.now(timezone.utc).isoformat(), intention, energy)
            payload = json.dumps({"ok": True}).encode()
            self.send_response(201)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        except (ValueError, json.JSONDecodeError):
            self.send_error(400, "Enter an intention and energy level.")


class LocalDashboardServer(ThreadingHTTPServer):
    """A small loopback-only server that can restart cleanly between app launches."""

    allow_reuse_address = True
    daemon_threads = True


def serve(port: int = 8765) -> ThreadingHTTPServer:
    return LocalDashboardServer(("127.0.0.1", port), Handler)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dashboard-only", action="store_true")
    parser.add_argument("--interval", type=float, default=1.0)
    args = parser.parse_args()
    storage.initialize()
    tracker = None if args.dashboard_only else ActivityTracker(args.interval)
    if tracker:
        tracker.start()
        print(f"Tracking meaningful window changes every {args.interval}s. Press Ctrl+C to stop.")
    server = serve()
    print("Dashboard: http://127.0.0.1:8765")
    try:
        server.serve_forever()
    finally:
        if tracker:
            tracker.stop()


if __name__ == "__main__":
    main()

