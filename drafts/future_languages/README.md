# Future languages (not part of the pilot)

The pilot covers **English and Taglish** only (decided Oct 2, 2026). These sheets are kept as a
starting point for the next phase. That phase needs native Chinoy collaborators to write or
review the prompts.

| File | What it is | Status |
|---|---|---|
| `zh_hant.yaml` | Chinoy (Filipino-Chinese) Mandarin, Traditional script | Claude draft, **not reviewed**. Do not use as-is. |
| `zh_hans.yaml` | Same text converted to Simplified (OpenCC t2s), for a script-only contrast | Claude draft, **not reviewed** |
| `nan.yaml` | Chinoy Hokkien/English in informal texting romanization: framings + T01, T14 for a comprehension test | Blank, to be written by a Chinoy speaker |

Why they were deferred: the author speaks Chinoy Mandarin and Hokkien conversationally but isn't
an expert writer of either, and the Mandarin drafts were written by Claude, which is also one of
the audited models. Prompts that don't read like real Chinoy novices would confound RQ3.

To bring one back: move it into `prompts/` and run `uv run python scripts/check_translations.py`.
Re-add the `opencc-python-reimplemented` dev dependency if you need to regenerate `zh_hans.yaml`.
