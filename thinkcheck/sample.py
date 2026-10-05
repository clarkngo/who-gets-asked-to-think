"""Build the hand-coding sets (deterministic: same seed, same sample).

Usage:
    uv run python -m thinkcheck.sample        # writes data/coding/items_v1.json

Two sets:
- "review": every Claude "help me learn" Taglish response that the checker left as no_function
  or fail. One question: does it contain a complete, runnable solution?
- "coding": a stratified sample for the codebook. The same 17 tasks (randomly chosen from 20) in
  each of the 12 cells (3 models x 2 framings x 2 languages), with one rep picked at random per
  task and cell, giving 204 responses. Every cell is equally represented and covers the same
  tasks, so differences between cells aren't differences in task mix.
  The first 10 items in coding order are a calibration round spanning 10 different cells; the
  rest are shuffled. The coder never sees the model, rep, or checker result.
"""
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED = 20261005
SAMPLE_VERSION = 1
TASKS_PER_CELL = 17
CALIBRATION_SIZE = 10
MODELS = ["ollama_qwen2.5_7b", "google_gemini-3.8-flash", "anthropic_claude-sonnet-5-5"]
FRAMINGS = ["make", "learn"]
LANGUAGES = ["en", "tl"]


def _load(path):
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _item(r, item_set, item_id):
    return {
        "item_id": item_id,
        "set": item_set,
        "model_key": r["model_key"],        # never shown in the coding app
        "prompt_id": r["prompt_id"],
        "rep": r["rep"],
        "task_id": r["task_id"],
        "framing": r["framing"],
        "language": r["language"],
        "prompt_text": r["prompt_text"],
        "response_text": r["response_text"],
    }


def build():
    rng = random.Random(SEED)
    raw = {m: {(r["prompt_id"], r["rep"]): r for r in _load(ROOT / "data" / "raw" / f"{m}.jsonl") if r["error"] is None}
           for m in MODELS}
    tasks = sorted({r["task_id"] for r in raw[MODELS[0]].values()})
    chosen_tasks = sorted(rng.sample(tasks, TASKS_PER_CELL))

    cells = [(m, f, l) for m in MODELS for f in FRAMINGS for l in LANGUAGES]
    coding = []
    for m, f, l in cells:
        for t in chosen_tasks:
            rep = rng.randrange(3)
            coding.append(raw[m][(f"{t}-{f}-{l}", rep)])
    # Calibration: one response from each of 10 different cells, then the rest shuffled.
    rng.shuffle(coding)
    calibration, seen = [], set()
    for r in coding:
        cell = (r["model_key"], r["framing"], r["language"])
        if cell not in seen and len(calibration) < CALIBRATION_SIZE:
            calibration.append(r)
            seen.add(cell)
    rest = [r for r in coding if r not in calibration]
    ordered = calibration + rest
    coding_items = [_item(r, "coding", f"C{i:03d}") for i, r in enumerate(ordered, 1)]
    for it in coding_items[:CALIBRATION_SIZE]:
        it["calibration"] = True

    checks = {(c["prompt_id"], c["rep"]): c for c in _load(ROOT / "data" / "derived" / "checks" / "anthropic_claude-sonnet-5-5.jsonl")}
    review_src = [r for k, r in sorted(raw["anthropic_claude-sonnet-5-5"].items())
                  if r["framing"] == "learn" and r["language"] == "tl" and checks[k]["status"] in ("no_function", "fail")]
    review_items = [_item(r, "review", f"R{i:02d}") for i, r in enumerate(review_src, 1)]

    return {
        "sample_version": SAMPLE_VERSION,
        "seed": SEED,
        "tasks_in_coding_sample": chosen_tasks,
        "items": review_items + coding_items,
    }


def main():
    data = build()
    out = ROOT / "data" / "coding" / f"items_v{SAMPLE_VERSION}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    n_review = sum(i["set"] == "review" for i in data["items"])
    n_coding = sum(i["set"] == "coding" for i in data["items"])
    print(f"wrote {out.relative_to(ROOT)}: {n_review} review + {n_coding} coding items "
          f"(tasks: {', '.join(data['tasks_in_coding_sample'])})")


if __name__ == "__main__":
    main()
