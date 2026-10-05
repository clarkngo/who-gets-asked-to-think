import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from thinkcheck import coding_server as cs


@pytest.fixture
def server(tmp_path):
    cs.Handler.items = {
        "R01": {"item_id": "R01", "set": "review", "model_key": "anthropic:x", "rep": 2, "task_id": "T01",
                "framing": "learn", "language": "tl", "prompt_text": "p", "response_text": "r"},
        "C001": {"item_id": "C001", "set": "coding", "calibration": True, "model_key": "google:y", "rep": 0,
                 "task_id": "T02", "framing": "make", "language": "en", "prompt_text": "p", "response_text": "r"},
    }
    cs.Handler.codes_path = tmp_path / "codes.json"
    cs.Handler.meta = {"coder": "test"}
    srv = ThreadingHTTPServer(("127.0.0.1", 0), cs.Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}", tmp_path / "codes.json"
    srv.shutdown()


def post(url, body):
    req = urllib.request.Request(url + "/api/codes", data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    return urllib.request.urlopen(req)


def test_items_are_blinded(server):
    url, _ = server
    items = json.load(urllib.request.urlopen(url + "/api/items"))["items"]
    assert all("model_key" not in i and "rep" not in i for i in items)


def test_codes_are_saved_to_disk(server):
    url, path = server
    post(url, {"item_id": "C001", "C1": True, "C6": False, "notes": "explains modulo"})
    post(url, {"item_id": "R01", "complete_solution": "no"})
    saved = json.loads(path.read_text())["codes"]
    assert saved["C001"]["C1"] is True and saved["C001"]["notes"] == "explains modulo"
    assert saved["R01"]["complete_solution"] == "no" and "coded_at" in saved["R01"]


def test_bad_input_is_rejected(server):
    url, path = server
    for bad in ({"item_id": "nope"}, {"item_id": "C001", "C1": "yes"}, {"item_id": "R01", "complete_solution": "maybe"}):
        with pytest.raises(urllib.error.HTTPError) as e:
            post(url, bad)
        assert e.value.code == 400
    assert not path.exists()
