"""Check the translation sheets in prompts/ against the canonical English (prompts/en.yaml).

Usage:
    uv run python scripts/check_translations.py            # checks every sheet
    uv run python scripts/check_translations.py tl         # one language
    uv run python scripts/check_translations.py path.yaml  # a specific file

Errors (exit code 1) are things that would break or confound the study:
  - a keep_verbatim item (function name, example call, quoted value) is missing or altered
  - a framing doesn't contain {spec} exactly once
  - a task is missing, or a status is not todo/draft/final
  - an item is marked final but its provenance is still claude-draft (Clark must review it)
Warnings are worth a look but don't block anything.
"""
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PROMPTS = ROOT / "prompts"
STATUSES = {"todo", "draft", "final"}
# Who produced the current text. Reported in the write-up, so keep it accurate.
PROVENANCES = {"claude-draft", "clark-reviewed", "clark-edited", "clark-written"}
CJK = re.compile(r"[一-鿿]")
LOOKALIKES = "“”‘’，：（）［］｛｝"


def norm(text):
    return (text or "").strip()


def flatten(text):
    """Join wrapped lines within a paragraph, as the prompt builder does before sending.

    Lines are joined with a space, or with nothing when either side is a CJK character.
    Blank lines (paragraph breaks) are kept.
    """
    paragraphs = re.split(r"\n\s*\n", norm(text))
    out = []
    for para in paragraphs:
        lines = [line.strip() for line in para.split("\n") if line.strip()]
        joined = lines[0] if lines else ""
        for line in lines[1:]:
            sep = "" if CJK.match(joined[-1]) or CJK.match(line[0]) else " "
            joined += sep + line
        out.append(joined)
    return "\n\n".join(out)


def check_item(label, english_now, item, keep, is_framing, lang, errors, warnings):
    status = item.get("status")
    provenance = item.get("provenance")
    translation = flatten(item.get("translation"))
    english_now = flatten(english_now)
    if status not in STATUSES:
        errors.append(f"{label}: status is {status!r}; use todo, draft, or final")
        return status
    if flatten(item.get("english")) != english_now:
        warnings.append(f"{label}: English source changed since this sheet was made. Re-check the translation")
    if status == "todo":
        if translation and translation != "TODO":
            warnings.append(f"{label}: has a translation but status is still 'todo'")
        return status
    if not translation or translation == "TODO":
        errors.append(f"{label}: status is {status} but translation is empty/TODO")
        return status
    if provenance not in PROVENANCES:
        errors.append(f"{label}: provenance is {provenance!r}; use one of {sorted(PROVENANCES)}")
    elif status == "final" and provenance == "claude-draft":
        errors.append(f"{label}: marked final but provenance is claude-draft. Set it to "
                      "clark-reviewed (no changes) or clark-edited once you've checked it")

    if is_framing:
        n = translation.count("{spec}")
        if n != 1:
            errors.append(f"{label}: must contain {{spec}} exactly once (found {n})")
    for k in dict.fromkeys(keep):
        need, have = english_now.count(k), translation.count(k)
        if have < need:
            hint = ""
            if any(ch in translation for ch in LOOKALIKES):
                hint = " (full-width or curly punctuation found; code must use ASCII \" , : ( ) [ ] { })"
            errors.append(f"{label}: must keep {k} exactly ({need}x in English, {have}x here){hint}")

    if lang.startswith("zh") and not CJK.search(translation):
        warnings.append(f"{label}: no Chinese characters found. Is it translated?")
    if translation == english_now:
        warnings.append(f"{label}: identical to English")
    return status


def check_file(path):
    en = yaml.safe_load((PROMPTS / "en.yaml").read_text(encoding="utf-8"))
    sheet = yaml.safe_load(path.read_text(encoding="utf-8"))
    lang = sheet.get("language", path.stem)
    errors, warnings, statuses = [], [], Counter()

    for name, english_now in en["framings"].items():
        item = (sheet.get("framings") or {}).get(name)
        if item is None:
            errors.append(f"framing {name}: missing")
            continue
        statuses[check_item(f"framing {name}", english_now, item, [], True, lang, errors, warnings)] += 1

    sheet_tasks = sheet.get("tasks") or {}
    # A sheet may cover only some tasks (e.g. the Hokkien comprehension test) by listing them in `subset`.
    subset = sheet.get("subset")
    required = {tid: task for tid, task in en["tasks"].items() if subset is None or tid in subset}
    for tid, task in required.items():
        item = sheet_tasks.get(tid)
        if item is None:
            errors.append(f"{tid}: missing")
            continue
        statuses[check_item(tid, task["spec"], item, task["keep_verbatim"], False, lang, errors, warnings)] += 1
    for tid in sheet_tasks:
        if tid not in en["tasks"]:
            warnings.append(f"{tid}: not in en.yaml (extra task?)")

    total = len(en["framings"]) + len(required)
    summary = ", ".join(f"{statuses[s]} {s}" for s in ("final", "draft", "todo"))
    shown = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path.name
    print(f"\n== {shown} ({lang}): {summary} (of {total})")
    for e in errors:
        print(f"  ERROR    {e}")
    for w in warnings:
        print(f"  warning  {w}")
    if not errors and not warnings:
        print("  all checks passed")
    return not errors


def main(argv):
    targets = argv or sorted(p.stem for p in PROMPTS.glob("*.yaml") if p.stem != "en")
    paths = [Path(t) if t.endswith(".yaml") else PROMPTS / f"{t}.yaml" for t in targets]
    ok = all([check_file(p.resolve()) for p in paths])
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main(sys.argv[1:])
