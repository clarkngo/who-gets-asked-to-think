"""Build the exact prompts sent to every model: tasks x framings x languages.

Usage:
    uv run python -m thinkcheck.prompts            # writes data/prompts.jsonl (en + tl)
    uv run python -m thinkcheck.prompts --print T01-learn-tl

English specs and framings come from prompts/en.yaml. Other languages come from their translation
sheets, and only items marked `final` are used, so a half-finished sheet can never leak into a run.
"""
import argparse
import hashlib
import json
from pathlib import Path

import yaml

from thinkcheck.text import flatten

ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = ROOT / "prompts"
PILOT_LANGUAGES = ("en", "tl")
FRAMINGS = ("make", "learn")


def _load(lang):
    return yaml.safe_load((PROMPTS_DIR / f"{lang}.yaml").read_text(encoding="utf-8"))


def _texts(lang, en):
    """Return ({framing: text}, {task_id: spec}) for a language."""
    if lang == "en":
        return dict(en["framings"]), {tid: t["spec"] for tid, t in en["tasks"].items()}
    sheet = _load(lang)
    not_final = [k for k, v in {**sheet["framings"], **sheet["tasks"]}.items() if v.get("status") != "final"]
    if not_final:
        raise ValueError(f"{lang}: items not final: {', '.join(not_final)}")
    framings = {k: v["translation"] for k, v in sheet["framings"].items()}
    specs = {tid: v["translation"] for tid, v in sheet["tasks"].items()}
    return framings, specs


def build_prompts(languages=PILOT_LANGUAGES):
    """Return one dict per prompt, in a stable order (task, framing, language)."""
    en = _load("en")
    per_lang = {lang: _texts(lang, en) for lang in languages}
    prompts = []
    for task_id, task in en["tasks"].items():
        for framing in FRAMINGS:
            for lang in languages:
                framings, specs = per_lang[lang]
                template = flatten(framings[framing])
                if template.count("{spec}") != 1:
                    raise ValueError(f"{lang} {framing}: framing must contain {{spec}} exactly once")
                text = template.replace("{spec}", flatten(specs[task_id]))
                prompts.append({
                    "prompt_id": f"{task_id}-{framing}-{lang}",
                    "task_id": task_id,
                    "function": task["function"],
                    "framing": framing,
                    "language": lang,
                    "text": text,
                    "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                })
    return prompts


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--languages", nargs="+", default=list(PILOT_LANGUAGES))
    parser.add_argument("--out", default=str(ROOT / "data" / "prompts.jsonl"))
    parser.add_argument("--print", metavar="PROMPT_ID", help="print one prompt's text and exit")
    args = parser.parse_args()

    prompts = build_prompts(args.languages)
    if args.print:
        match = [p for p in prompts if p["prompt_id"] == args.print]
        if not match:
            raise SystemExit(f"no prompt {args.print!r}")
        print(match[0]["text"])
        return
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for p in prompts:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    print(f"wrote {len(prompts)} prompts to {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
