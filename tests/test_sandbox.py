"""Integration tests: need Docker running, the sandbox image built, and the private hidden tests."""
import shutil
import subprocess

import pytest

from thinkcheck.sandbox import HIDDEN_TESTS_DIR, IMAGE, run_in_sandbox


def _ready():
    if not shutil.which("docker") or not HIDDEN_TESTS_DIR.exists():
        return False
    return subprocess.run(["docker", "image", "inspect", IMAGE], capture_output=True).returncode == 0


pytestmark = pytest.mark.skipif(not _ready(), reason="needs Docker, sandbox image, and hidden tests")

GOOD = "def split_bill(total, people, tip_percent):\n    return round(total * (1 + tip_percent / 100) / people, 2)\n"


def test_every_reference_solution_passes_all_hidden_tests():
    for ref in sorted((HIDDEN_TESTS_DIR / "reference").glob("t*.py")):
        task_id = ref.stem.split("_")[0].upper()
        r = run_in_sandbox(ref.read_text(), task_id, {})
        assert r["status"] == "pass", (task_id, r)


def test_wrong_code_fails_with_partial_credit():
    wrong = "def split_bill(total, people, tip_percent):\n    return round(total / people, 2)\n"  # ignores tip
    r = run_in_sandbox(wrong, "T01", {})
    assert r["status"] == "fail" and 0 < r["tests_passed"] < r["tests_total"]


def test_infinite_loop_is_cut_off():
    r = run_in_sandbox("def split_bill(t, p, x):\n    while True:\n        pass\n", "T01", {})
    assert r["status"] == "fail" and r["tests_passed"] == 0


def test_hang_at_import_is_an_import_error():
    r = run_in_sandbox("import time\ntime.sleep(60)\n" + GOOD, "T01", {})
    assert r["status"] == "import_error" and r["import"]["error_type"] == "Timeout"


def test_network_and_filesystem_writes_are_blocked():
    probes = {
        "network": "import socket\nsocket.create_connection(('1.1.1.1', 80), timeout=2)",
        "write_work": "open('/work/x.txt', 'w')",
        "write_root": "open('/etc/x', 'w')",
    }
    r = run_in_sandbox(GOOD, "T01", probes)
    assert r["status"] == "pass"
    assert all(not p["ok"] for p in r["probes"].values()), r["probes"]


def test_probes_record_values_and_exceptions():
    probes = {"zero_people": "split_bill(50, 0, 10)", "normal": "split_bill(10, 2, 0)"}
    r = run_in_sandbox(GOOD, "T01", probes)
    assert r["probes"]["zero_people"]["ok"] is False
    assert r["probes"]["zero_people"]["error_type"] == "ZeroDivisionError"
    assert r["probes"]["normal"]["repr"] == "5.0"
