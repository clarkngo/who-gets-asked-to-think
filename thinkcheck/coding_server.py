"""Local coding app: serves coding/app.html and saves every code straight to the repo.

Usage:
    uv run python -m thinkcheck.coding_server          # then open http://127.0.0.1:8765

Codes are written to data/coding/codes_v<sample>_<coder>.json after every change (atomic
write), so nothing lives only in the browser. Blinding: the app never receives the model or
rep of an item, only the prompt, the response, and the item's set/order.
"""
import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "coding" / "app.html"
CODES = ("C1", "C2", "C3", "C4", "C5", "C6")
SHOWN_FIELDS = ("item_id", "set", "calibration", "task_id", "framing", "language", "prompt_text", "response_text")


def load_items(sample_version):
    data = json.loads((ROOT / "data" / "coding" / f"items_v{sample_version}.json").read_text(encoding="utf-8"))
    return {i["item_id"]: i for i in data["items"]}


def validate(entry, item):
    """Return a clean code record, or raise ValueError."""
    clean = {"notes": str(entry.get("notes", ""))[:2000], "unsure": bool(entry.get("unsure", False))}
    if item["set"] == "review":
        if entry.get("complete_solution") not in ("yes", "no", "unsure", None):
            raise ValueError("complete_solution must be yes/no/unsure")
        clean["complete_solution"] = entry.get("complete_solution")
    else:
        for c in CODES:
            if not isinstance(entry.get(c, False), bool):
                raise ValueError(f"{c} must be true/false")
            clean[c] = entry.get(c, False)
    return clean


class Handler(BaseHTTPRequestHandler):
    items: dict = {}
    codes_path: Path = None
    meta: dict = {}

    def _send(self, status, body, content_type="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _codes(self):
        if self.codes_path.exists():
            return json.loads(self.codes_path.read_text(encoding="utf-8"))
        return {"meta": self.meta, "codes": {}}

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            return self._send(200, APP.read_bytes(), "text/html")
        if self.path == "/api/items":
            shown = [{k: i.get(k) for k in SHOWN_FIELDS} for i in self.items.values()]
            return self._send(200, {"meta": self.meta, "items": shown})
        if self.path == "/api/codes":
            return self._send(200, self._codes())
        self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/api/codes":
            return self._send(404, {"error": "not found"})
        try:
            entry = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            item = self.items[entry["item_id"]]
            record = validate(entry, item)
        except (KeyError, ValueError, json.JSONDecodeError) as exc:
            return self._send(400, {"error": str(exc)})
        record["coded_at"] = datetime.now(timezone.utc).isoformat()
        data = self._codes()
        data["codes"][item["item_id"]] = record
        fd, tmp = tempfile.mkstemp(dir=self.codes_path.parent, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1, sort_keys=True)
        os.replace(tmp, self.codes_path)
        self._send(200, {"ok": True, "saved": len(data["codes"])})

    def log_message(self, fmt, *args):  # keep the terminal quiet
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--coder", default="clark")
    parser.add_argument("--sample-version", type=int, default=1)
    parser.add_argument("--codebook-version", default="v0")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    Handler.items = load_items(args.sample_version)
    Handler.codes_path = ROOT / "data" / "coding" / f"codes_v{args.sample_version}_{args.coder}.json"
    Handler.meta = {"coder": args.coder, "sample_version": args.sample_version,
                    "codebook_version": args.codebook_version}
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Coding app: http://127.0.0.1:{args.port}  (saving to {Handler.codes_path.relative_to(ROOT)}; Ctrl-C to stop)")
    server.serve_forever()


if __name__ == "__main__":
    main()
