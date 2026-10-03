import yaml

from thinkcheck.prompts import PROMPTS_DIR, build_prompts
from thinkcheck.text import flatten


def test_pilot_has_80_unique_prompts():
    prompts = build_prompts()
    assert len(prompts) == 20 * 2 * 2
    assert len({p["prompt_id"] for p in prompts}) == len(prompts)


def test_no_placeholders_or_todos_leak():
    for p in build_prompts():
        assert "{spec}" not in p["text"]
        assert "TODO" not in p["text"]


def test_every_prompt_keeps_code_literals_verbatim():
    en = yaml.safe_load((PROMPTS_DIR / "en.yaml").read_text(encoding="utf-8"))
    for p in build_prompts():
        for literal in en["tasks"][p["task_id"]]["keep_verbatim"]:
            assert literal in p["text"], (p["prompt_id"], literal)


def test_framing_differs_but_task_text_is_shared():
    prompts = {p["prompt_id"]: p["text"] for p in build_prompts()}
    make, learn = prompts["T01-make-en"], prompts["T01-learn-en"]
    assert make != learn
    spec = make.split("\n\n")[0]
    assert spec in learn


def test_flatten_joins_wrapped_lines_but_keeps_paragraphs():
    assert flatten("a b\nc d\n\ne f\n") == "a b c d\n\ne f"
    assert flatten("中文\n继续") == "中文继续"
