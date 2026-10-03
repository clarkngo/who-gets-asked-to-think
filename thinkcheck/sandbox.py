"""Run extracted code against a task's hidden tests inside a locked-down Docker container.

Isolation for every check: no network, read-only filesystem (code mounted read-only, small tmpfs
for /tmp), 256 MB memory, 1 CPU, 64 processes, all Linux capabilities dropped, no privilege
escalation, an unprivileged user, and a wall-clock limit (the container is killed on timeout).
"""
import hashlib
import json
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMAGE = "thinkcheck-sandbox:1"
HIDDEN_TESTS_DIR = ROOT / "drafts" / "sample_tasks"   # private, gitignored until the pilot is done
WORK_ROOT = ROOT / "sandbox_tmp"                      # gitignored; under /Users so Docker can mount it
WALL_TIMEOUT_S = 60
MARK = "@@THINKCHECK_RESULT@@"

DOCKER_FLAGS = [
    "--network", "none",
    "--read-only", "--tmpfs", "/tmp:rw,size=16m",
    "--memory", "256m", "--memory-swap", "256m",
    "--cpus", "1", "--pids-limit", "64",
    "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
    "--user", "65534:65534",
]


def test_file(task_id: str) -> Path:
    matches = sorted(HIDDEN_TESTS_DIR.glob(f"test_{task_id.lower()}_*.py"))
    if len(matches) != 1:
        raise FileNotFoundError(f"expected one hidden test file for {task_id} in {HIDDEN_TESTS_DIR}, found {len(matches)}")
    return matches[0]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def image_id() -> str:
    out = subprocess.run(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(f"sandbox image {IMAGE} not found; build it with: docker build -t {IMAGE} sandbox/")
    return out.stdout.strip()


def run_in_sandbox(code: str, task_id: str, probes: dict) -> dict:
    """Return {"status", "tests_passed", "tests_total", "tests", "import", "probes", ...}."""
    WORK_ROOT.mkdir(exist_ok=True)
    work = Path(tempfile.mkdtemp(dir=WORK_ROOT))
    name = f"thinkcheck-{uuid.uuid4().hex[:12]}"
    try:
        (work / "solution.py").write_text(code, encoding="utf-8")
        shutil.copy(test_file(task_id), work / "test_spec.py")
        (work / "probes.json").write_text(json.dumps(probes), encoding="utf-8")
        for p in work.iterdir():
            p.chmod(0o644)
        work.chmod(0o755)
        cmd = ["docker", "run", "--rm", "--name", name, *DOCKER_FLAGS,
               "-v", f"{work}:/work:ro", "-w", "/work", IMAGE]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=WALL_TIMEOUT_S)
        except subprocess.TimeoutExpired:
            subprocess.run(["docker", "kill", name], capture_output=True)
            return {"status": "timeout", "tests_passed": 0, "tests_total": None}
        line = next((l for l in reversed(proc.stdout.splitlines()) if l.startswith(MARK)), None)
        if line is None:
            return {"status": "crashed", "tests_passed": 0, "tests_total": None,
                    "returncode": proc.returncode, "stderr_tail": proc.stderr[-500:]}
        result = json.loads(line[len(MARK):])
    finally:
        shutil.rmtree(work, ignore_errors=True)

    if not result["import"]["ok"]:
        status = "import_error"
    else:
        passed = sum(t["outcome"] == "passed" for t in result["tests"])
        status = "pass" if result["tests"] and passed == len(result["tests"]) else "fail"
    return {
        "status": status,
        "tests_passed": sum(t["outcome"] == "passed" for t in result["tests"]),
        "tests_total": len(result["tests"]) or None,
        "tests": result["tests"],
        "import": result["import"],
        "pytest_exit": result["pytest_exit"],
        "probes": result["probes"],
    }
