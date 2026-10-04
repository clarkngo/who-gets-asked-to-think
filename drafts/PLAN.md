# ThinkCheck: plan (DRAFT v0)

> Working draft for Clark's review. Nothing has been built or committed yet.
> Today: Fri Oct 2, 2026. Pilot write-up due: **Sat Oct 24, 2026** (about 3 weeks).

## 0. Decisions log

| Date | Decision |
|---|---|
| Oct 2 | Languages: all three (EN, TL, ZH). Tagalog written as natural **Taglish**; Mandarin in **Simplified** characters. *(Superseded: see below.)* |
| Oct 2 | Models: **Claude Sonnet 5.5** + **Gemini** (exact model TBD, to be checked against current lineup) + **qwen2.5:7b** (local, Ollama). |
| Oct 2 | Budget: hard cap **$20 for Claude, $20 for Gemini**, enforced by the runner. |
| Oct 2 | MAKE framing stays neutral ("can you just write it for me? i just need it to work."), with no "no explanation". |
| Oct 2 | Pages: publish the whole repo root, with an `index.html` at the root (existing workflow kept). |
| Oct 2 | Hidden tests + reference solutions stay private (gitignored) until the pilot run is done. |
| Oct 2 | Mandarin condition is now **Chinoy (Filipino-Chinese) Mandarin**, replacing standard Mainland Mandarin. It mixes in English tech and everyday words, and comes in **two scripts**: Traditional (`zh_hant`, drafted) and Simplified (`zh_hans`, an OpenCC t2s conversion of zh_hant), so the two differ only in script. *(Superseded: see below.)* |
| Oct 2 | **Hokkien/English** (`nan`): Clark writes it in informal romanization mixed with English, the way Chinoys text. First a comprehension test (2 framings + T01, T14; each model is asked to translate the prompts into English, and Clark judges whether it understood). Whether it becomes an exploratory 8-task condition depends on the result. *(Superseded: see below.)* |
| Oct 2 | Claude drafts the Taglish and Mandarin translations, and Clark reviews and edits every item. Each item records `provenance` (claude-draft → clark-reviewed / clark-edited), and the write-up reports the counts as a limitation (Claude is also an audited model). *(Superseded: see below.)* |
| Oct 2 | Taglish restarted from a **blank sheet that Clark writes from scratch** (`provenance: clark-written`). No Claude draft is used. |
| Oct 2 | **Pilot = English + Taglish only.** Chinoy Mandarin and Hokkien move to future work (`drafts/future_languages/`): Clark speaks them conversationally but isn't an expert writer, and AI-drafted prompts would confound RQ3. Standard Mandarin is also out (Clark's Mandarin is conversational/business, not computer science). These become the "next step" framed in the SOP. |
| Oct 2 | **Taglish sheet final** (22/22, all `clark-written`). Each item was compared against the English spec with Claude's help; Clark revised the items where meaning or wording diverged (T01, T04, T05, T06, T09, T14, T17, T18) and fixed typos and grammar slips. The write-up should describe this review. |
| Oct 2 | Hand coding: a fixed **stratified sample of ~200 responses** (not a %), balanced across model × framing × language. |
| Oct 3 | T04's within-list case test (`{"Tea": 1, "TEA": 2}` → `{"tea": 3}`) moved from scored tests to an **unscored probe**. The prompt never states that case, and scored tests check only what the prompt states. T13's banned-list case test stays scored, since "when checking" covers it. |
| Oct 3 | **Gemini = `gemini-3.8-flash`** (Google's recommended Flash model, checked Oct 3), provider defaults (thinking on at its default level), **free tier**: nothing charged, list-price cost logged (~$1.32 for 240 calls). On the free tier Google may use prompts to improve its products; state this in the write-up. |
| Oct 3 | **Extraction rule v2** (checker_version 2): top-level assignments are kept only if every name they use is already defined; definitions that never return a value are skipped when another definition exists; `has_placeholder` flags likely scaffolds (recorded, not scored). Triggered by Gemini's teaching responses (fragments like `period = parts[1]`, "add this line" snippets). Effect: qwen 0 status changes; Gemini 12 responses misjudged under v1 become pass. |

## 1. What's in the repo now

- `README.md`: title only.
- `.github/workflows/static.yml`: the stock GitHub Pages workflow. **It uploads the whole repo
  (`path: '.'`)**, so every file pushed to `main`, including raw data and drafts, would be
  served on the site. I suggest pointing it at `docs/` only (see Q-c).
- There's no `.gitignore` yet, so one has to go in **before** any `.env` file exists.
- Your machine (useful for planning): Python 3.12, `uv`, Docker, pandoc, typst, and Ollama with
  `qwen2.5:7b`, `qwen3.5:9b`, `llama3.1:8b`, `mistral:7b`, and `mistral-nemo:12b` already pulled,
  on 16 GB RAM.

## 2. Proposed folder structure

```
who-gets-asked-to-think/
├── README.md                  # RQs, method, reproduce, limitations
├── pyproject.toml, uv.lock    # pinned deps (uv)
├── .env.example               # ANTHROPIC_API_KEY=  (real .env is gitignored)
├── .gitignore
├── scripts/check_secrets.sh   # run by a pre-commit hook + before every commit I make
│
├── tasks/                     # the instrument
│   └── T01_split_bill/
│       ├── task.yaml          # id, function name, concepts, difficulty, probes
│       ├── test_spec.py       # hidden, scored tests
│       └── reference.py       # proves the tests are passable
├── prompts/
│   ├── en.yaml                # CANONICAL English specs + framings + keep_verbatim lists
│   ├── tl.yaml                # Taglish sheet (Clark-written), checked by scripts/check_translations.py
├── codebook/
│   ├── codebook.md            # human-readable, versioned (v0, v1, …)
│   └── codebook.yaml          # same content, machine-readable (for LLM pre-coding)
│
├── thinkcheck/                # the pipeline (Python package)
│   ├── models/                # pluggable: base.py, anthropic.py, ollama.py, (+ more later)
│   ├── build_prompts.py       # tasks × framings × languages → prompts.jsonl
│   ├── run.py                 # prompts × models × reps → data/raw/*.jsonl (resumable)
│   ├── extract.py             # pull the solution code out of each response
│   ├── sandbox.py             # Docker, --network none, CPU/mem/time limits
│   ├── check.py               # spec tests + probes → data/derived/checks.jsonl
│   ├── sample.py              # stratified sample for hand coding
│   ├── llm_code.py            # optional LLM pre-coding
│   └── agreement.py           # Cohen's κ per code, LLM vs Clark
├── data/
│   ├── raw/                   # append-only JSONL, never edited by hand
│   ├── coding/                # coding sheets (CSV) + Clark's completed codes
│   └── derived/               # everything here is regenerable from raw/ + coding/
├── analysis/
│   ├── analyze.py             # → tables + figures, rerunnable end to end
│   └── figures/
├── paper/
│   ├── pilot-writeup.md       # → pilot-writeup.pdf (pandoc + typst)
│   └── references.bib
├── docs/                      # GitHub Pages site (static HTML, charts, PDF, data link)
└── tests/                     # tests for the pipeline itself (extractor, sandbox, κ)
```

Every raw record (one JSON line per call) stores: `run_id, prompt_id, task_id, framing,
language, model_provider, model_id (as returned by the API), requested params, effective
params, rep, timestamp_utc, latency_ms, input/output tokens, stop_reason, full response text,
SDK + package versions, git commit of the repo`.

## 3. Step-by-step plan with time estimates

"Me" = Claude working in this repo. "You" = your hands-on time.

| # | Step | Me | You | Target date |
|---|------|----|-----|-------------|
| 0 | Repo hygiene: `.gitignore`, `.env.example`, secret-check hook, pin deps, restrict Pages to `docs/` | 1 h | 10 min review | Oct 3 |
| 1 | Finalise tasks 1–5 from your feedback, draft tasks 6–20 + tests + references | 3 h | 2–3 h review | Oct 5 |
| 2 | **You** write the Taglish specs and framings (22 items) | – | 3–4 h | Oct 8 |
| 3 | Model layer + runner + JSONL logging + cost meter; unit tests | 3 h | – | Oct 6 |
| 4 | Code extractor + Docker sandbox + checker; validate on references + deliberately broken code | 3 h | – | Oct 7 |
| 5 | **Dry run:** 2 tasks × all conditions; measure real tokens → updated cost estimate | 1 h | **approve cost** | Oct 8 |
| 6 | Full pilot run | ~1–2 h wall clock | – | Oct 9 |
| 7 | Codebook v1: you and I go through ~10 real responses together, then revise definitions | 1 h | 1.5 h | Oct 10 |
| 8 | **You** hand-code a stratified sample of ~200 responses (balanced across model × framing × language) | 1 h (tooling) | ~7 h | Oct 14 |
| 9 | (Optional) LLM pre-codes everything; κ vs your codes per code; decide what's reportable | 2 h | 30 min decide | Oct 15 |
| 10 | Analysis scripts + figures (descriptive; small-n, so no significance theatre) | 3 h | 1 h review | Oct 17 |
| 11 | Write-up draft (4–6 pp) → PDF | 3 h | 3–4 h edit | Oct 21 |
| 12 | Pages site + README final | 3 h | 1 h review | Oct 22 |
| – | Buffer | | | Oct 23–24 |

**Your total ≈ 17–24 hours over 3 weeks.** The critical path runs through *your* steps 2 and
8, so I'll make sure the pipeline is never what's holding them up.

## 4. Cost estimate (Claude API, before anything runs)

Pilot = 20 tasks × 2 framings × 2 languages (EN, Taglish) = **80 prompts per model**, × 3 reps = **240 calls per model** (720 responses across the 3 models). Assumptions (deliberately
pessimistic): ~250 input tokens, and up to ~3,000 billed output tokens per call (visible answer
plus thinking, which can't be switched off on current Claude models). Current list prices:

| Model | $/M in · out | 240 calls | 240 calls via Batch API |
|---|---|---|---|
| **Claude Sonnet 5.5** (chosen) | $2 · $10 | ~$7.30 | ~$3.70 |
| Gemini (model TBD) | TBD | TBD (to be checked) | TBD |
| qwen2.5:7b (local) | free | $0 | $0 |

Both caps are $20 per provider, enforced by the runner.

The optional LLM pre-coding (step 9) adds roughly $2–5. The Batch API halves every Claude figure. **Running ThinkCheck
costs under $30, so cost doesn't constrain which model we pick.** I'll replace these
numbers with measured ones after the dry run (step 5), and nothing runs before you approve.

## 5. Things you should know before deciding

1. **API ≠ product.** Students meet these models through apps (Claude.ai, ChatGPT, Copilot)
   that add their own system prompts. Calling the bare API audits *the models*, not *the
   products*. I'd send no system prompt, say so plainly, and title the claim accordingly
   ("AI models used as coding assistants").
2. **Temperature can't be set on current Claude models** (Opus 5.5 / Sonnet 5.5 reject sampling
   parameters, and thinking is always on). We'll record "provider default" plus the `effort`
   level, and run **3 repetitions per cell** so the analysis can show within-model variability.
   For Ollama we set `temperature` and `seed` explicitly.
3. **Local model choice.** qwen2.5:7b is developed in China; Llama/Mistral are US/EU. With an
   English–Taglish pilot this matters less than it did with Mandarin, but whichever we pick
   becomes part of the language story, and the write-up must name the confound.
4. **Correctness depends on the extractor.** If a response contains several code blocks, which
   one counts? Proposed rule: the last block that defines the required function. "No complete
   solution" is its own outcome, not "fail". (This matters for LEARN responses that scaffold.)
5. **Probes are unscored**, so models aren't penalised for reasonable choices on unspecified
   edge cases.

## 6. Open questions (beyond the three in chat)

- ~~Q1. Pilot languages~~ → **decided: English + Taglish** (see decisions log).
- **Q2. MAKE framing strength:** neutral ("can you just write it for me?") or explicitly
  code-only ("just the code, no explanation")?
- **Q3. Tagalog register:** formal Tagalog, or natural Taglish? (Taglish is more realistic for
  novices, but "language" then partly means "code-switching".) Mandarin: simplified or
  traditional characters?
- **Q4. Repetitions:** 3 per cell (recommended) or 1?
- **Q5. Effort level for Claude:** provider default, or a fixed value recorded explicitly?
- **Q6. Hand-coding sample size:** ~25–30% stratified, or all responses if the pilot is small
  enough?
