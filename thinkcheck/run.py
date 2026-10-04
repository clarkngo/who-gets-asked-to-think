"""Send every prompt to a model and append the raw responses to JSONL.

Usage:
    uv run python -m thinkcheck.run --model ollama:qwen2.5:7b                 # full run, 3 reps
    uv run python -m thinkcheck.run --model ollama:qwen2.5:7b --only T01 --reps 1   # quick check

Properties that matter for the study:
- Append-only: data/raw/<model>.jsonl is never rewritten. Analysis reads it as-is.
- Resumable: a (prompt, rep) that already has a successful record is skipped, so an interrupted
  run continues where it stopped and never double-counts.
- Balanced if interrupted: all prompts are done for rep 0 before rep 1 starts, and so on.
- Stops after 3 failed calls in a row (e.g. an exhausted free-tier daily quota); rerun later.
- Budget stop: before each paid call, the runner checks that spend so far plus the worst-case
  cost of one more call stays under the provider's cap. Failed calls are logged, not retried
  in the same run.
"""
import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from thinkcheck.models import get_model
from thinkcheck.prompts import PILOT_LANGUAGES, ROOT, build_prompts

SCHEMA_VERSION = 1
# Hard caps in USD per provider (decided Oct 2, 2026). Local models are free.
BUDGET_USD = {"anthropic": 20.0, "google": 20.0, "ollama": 0.0}
MAX_CONSECUTIVE_ERRORS = 3


def seed_for(prompt_id: str, rep: int) -> int:
    """A fixed seed per (prompt, rep), so local runs are reproducible."""
    return int(hashlib.sha256(f"{prompt_id}|{rep}".encode()).hexdigest()[:8], 16)


def raw_path(model_key: str) -> Path:
    slug = model_key.replace(":", "_").replace("/", "_")
    return ROOT / "data" / "raw" / f"{slug}.jsonl"


def read_records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def environment() -> dict:
    def version(pkg):
        try:
            return importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError:
            return None

    def git(*args):
        try:
            return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return None

    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": {p: version(p) for p in ("anthropic", "google-genai", "ollama")},
        "git_commit": git("rev-parse", "HEAD"),
        "git_dirty": bool(git("status", "--porcelain", "--", "thinkcheck", "prompts")),
    }


def run(model, prompts, reps, out: Path, budget: float, log=print) -> dict:
    """Run every (prompt, rep) not already done. Returns counts for reporting."""
    existing = read_records(out)
    done = {(r["prompt_id"], r["rep"]) for r in existing if r.get("error") is None}
    spent = sum(r.get("cost_usd") or 0.0 for r in existing)
    description = model.describe()
    env = environment()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    todo = [(rep, p) for rep in range(reps) for p in prompts if (p["prompt_id"], rep) not in done]
    counts = {"skipped_done": len(prompts) * reps - len(todo), "ok": 0, "error": 0, "budget_stop": False,
              "error_stop": False}
    consecutive_errors = 0
    log(f"{model.key}: {len(todo)} calls to make ({counts['skipped_done']} already done), "
        f"spent so far ${spent:.4f} of ${budget:.2f} cap")

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as f:
        for i, (rep, p) in enumerate(todo, 1):
            worst = model.max_cost_per_call()
            if worst > 0 and spent + worst > budget:
                counts["budget_stop"] = True
                log(f"BUDGET STOP: ${spent:.4f} spent; one more call could cost up to ${worst:.4f}")
                break
            seed = seed_for(p["prompt_id"], rep)
            started = datetime.now(timezone.utc)
            t0 = time.monotonic()
            record = {
                "schema_version": SCHEMA_VERSION,
                "run_id": run_id,
                "prompt_id": p["prompt_id"],
                "task_id": p["task_id"],
                "function": p["function"],
                "framing": p["framing"],
                "language": p["language"],
                "prompt_text": p["text"],
                "prompt_sha256": p["sha256"],
                "rep": rep,
                "seed": seed,
                "model_key": model.key,
                "model": description,
                "started_at": started.isoformat(),
            }
            try:
                g = model.generate(p["text"], seed)
                record.update({
                    "response_text": g.text,
                    "model_id": g.model_id,
                    "stop_reason": g.stop_reason,
                    "input_tokens": g.input_tokens,
                    "output_tokens": g.output_tokens,
                    "cost_usd": g.cost_usd,
                    "provider_extra": g.extra,
                    "error": None,
                })
                spent += g.cost_usd
                counts["ok"] += 1
                consecutive_errors = 0
            except Exception as exc:  # noqa: BLE001 - logged and kept; the next run retries it
                record.update({"response_text": None, "cost_usd": 0.0, "error": f"{type(exc).__name__}: {exc}"})
                counts["error"] += 1
                consecutive_errors += 1
            record["finished_at"] = datetime.now(timezone.utc).isoformat()
            record["latency_ms"] = round((time.monotonic() - t0) * 1000)
            record["environment"] = env
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()
            status = "ok" if record["error"] is None else f"ERROR {record['error'][:80]}"
            log(f"[{i}/{len(todo)}] rep {rep} {p['prompt_id']}: {status} "
                f"({record['latency_ms'] / 1000:.1f}s, {record.get('output_tokens')} tokens)")
            if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                counts["error_stop"] = True
                log(f"STOPPING after {consecutive_errors} failed calls in a row; rerun later to continue")
                break
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", required=True, help="e.g. ollama:qwen2.5:7b")
    parser.add_argument("--reps", type=int, default=3)
    parser.add_argument("--languages", nargs="+", default=list(PILOT_LANGUAGES))
    parser.add_argument("--only", nargs="+", metavar="ID",
                        help="restrict to task IDs (T01) or prompt IDs (T01-make-en)")
    parser.add_argument("--out", help="output JSONL (default data/raw/<model>.jsonl)")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    model = get_model(args.model)
    prompts = build_prompts(args.languages)
    if args.only:
        prompts = [p for p in prompts if p["task_id"] in args.only or p["prompt_id"] in args.only]
        if not prompts:
            raise SystemExit(f"no prompts match {args.only}")
    out = Path(args.out) if args.out else raw_path(model.key)
    counts = run(model, prompts, args.reps, out, BUDGET_USD.get(model.provider, 0.0))
    print(json.dumps(counts))
    sys.exit(1 if counts["error"] or counts["budget_stop"] or counts["error_stop"] else 0)


if __name__ == "__main__":
    main()
