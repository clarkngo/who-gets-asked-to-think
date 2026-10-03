"""Runs INSIDE the sandbox container. Reads /work (mounted read-only):
    solution.py   extracted model code
    test_spec.py  hidden spec tests for the task
    probes.json   {name: python source}; last line's value is recorded
Prints one line: MARK + JSON result. Everything the solution prints is swallowed.
"""
import contextlib
import io
import json
import signal
import sys

MARK = "@@THINKCHECK_RESULT@@"
IMPORT_TIMEOUT_S = 5
TEST_TIMEOUT_S = 5
PROBE_TIMEOUT_S = 3


class Timeout(Exception):
    pass


def _alarm(signum, frame):
    raise Timeout("time limit exceeded")


def _short(exc):
    return {"error_type": type(exc).__name__, "message": str(exc)[:200]}


class Collector:
    def __init__(self):
        self.tests = []

    def pytest_runtest_logreport(self, report):
        # One entry per test: its call phase, or the phase that went wrong.
        if report.when == "call" or report.outcome != "passed":
            self.tests.append({
                "test": report.nodeid.split("::")[-1],
                "phase": report.when,
                "outcome": report.outcome,
                "detail": (str(report.longrepr).strip().splitlines() or [""])[-1][:200] if report.failed else None,
            })


def main():
    sys.path.insert(0, "/work")
    signal.signal(signal.SIGALRM, _alarm)
    result = {"import": None, "tests": [], "pytest_exit": None, "probes": {}}

    try:
        signal.alarm(IMPORT_TIMEOUT_S)
        with contextlib.redirect_stdout(io.StringIO()):
            import solution
        result["import"] = {"ok": True}
    except BaseException as exc:  # noqa: BLE001 - includes SystemExit, Timeout
        result["import"] = {"ok": False, **_short(exc)}
    finally:
        signal.alarm(0)

    if result["import"]["ok"]:
        import pytest

        collector = Collector()
        with contextlib.redirect_stdout(io.StringIO()):
            code = pytest.main(["-q", "-p", "no:cacheprovider", f"--timeout={TEST_TIMEOUT_S}",
                                "/work/test_spec.py"], plugins=[collector])
        result["tests"] = collector.tests
        result["pytest_exit"] = int(code)

        with open("/work/probes.json", encoding="utf-8") as f:
            probes = json.load(f)
        for name, source in probes.items():
            namespace = dict(vars(solution))
            lines = source.strip().split("\n")
            try:
                signal.alarm(PROBE_TIMEOUT_S)
                with contextlib.redirect_stdout(io.StringIO()):
                    if len(lines) > 1:
                        exec("\n".join(lines[:-1]), namespace)
                    value = eval(lines[-1], namespace)
                result["probes"][name] = {"ok": True, "type": type(value).__name__, "repr": repr(value)[:200]}
            except BaseException as exc:  # noqa: BLE001
                result["probes"][name] = {"ok": False, **_short(exc)}
            finally:
                signal.alarm(0)

    sys.stdout.write(MARK + json.dumps(result) + "\n")


if __name__ == "__main__":
    main()
