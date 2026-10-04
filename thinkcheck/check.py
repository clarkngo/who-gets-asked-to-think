"""Check the code in every raw response: extract it, run it against the hidden tests, record probes.

Usage:
    uv run python -m thinkcheck.check data/raw/ollama_qwen2.5_7b.jsonl
    # writes data/derived/checks/ollama_qwen2.5_7b.jsonl (regenerated from scratch each time)

Status per response:
    pass | fail          extracted and ran; all / not all hidden tests passed
    import_error         the extracted code crashed or hung when loaded
    timeout | crashed    the sandbox container hit the wall-clock limit / died (e.g. memory)
    no_code | unparseable | no_function   nothing runnable to test (see thinkcheck/extract.py)
"""
import argparse
import hashlib
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

from thinkcheck.extract import extract
from thinkcheck.sandbox import ROOT, image_id, run_in_sandbox, sha256, test_file

CHECKER_VERSION = 2  # v2: extraction rule refinements (see thinkcheck/extract.py)
PROBES_FILE = ROOT / "tasks" / "probes.yaml"


def check_record(record: dict, probes: dict, image: str) -> dict:
    ex = extract(record["response_text"], record["function"])
    out = {
        "checker_version": CHECKER_VERSION,
        "model_key": record["model_key"],
        "prompt_id": record["prompt_id"],
        "rep": record["rep"],
        "task_id": record["task_id"],
        "framing": record["framing"],
        "language": record["language"],
        "extraction": {k: v for k, v in vars(ex).items() if k != "code"},
        "code_sha256": None,
        "sandbox_image": image,
        "tests_sha256": sha256(test_file(record["task_id"])),
    }
    if ex.status != "ok":
        out.update({"status": ex.status, "tests_passed": 0, "tests_total": None})
        return out
    out["code_sha256"] = hashlib.sha256(ex.code.encode()).hexdigest()
    out.update(run_in_sandbox(ex.code, record["task_id"], probes.get(record["task_id"], {})))
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("raw", help="raw JSONL from thinkcheck.run")
    parser.add_argument("--out", help="default: data/derived/checks/<same name>")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    raw = Path(args.raw)
    records = [json.loads(l) for l in raw.read_text(encoding="utf-8").splitlines() if l.strip()]
    records = [r for r in records if r.get("error") is None]
    probes = yaml.safe_load(PROBES_FILE.read_text(encoding="utf-8"))
    image = image_id()
    out = Path(args.out) if args.out else ROOT / "data" / "derived" / "checks" / raw.name

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(lambda r: check_record(r, probes, image), records))
    results.sort(key=lambda r: (r["rep"], r["prompt_id"]))

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"checked {len(results)} responses -> {out.relative_to(ROOT)}")
    print(json.dumps(dict(Counter(r["status"] for r in results))))


if __name__ == "__main__":
    main()
