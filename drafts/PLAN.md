# ThinkCheck: plan (DRAFT v0)

> Working draft for Clark's review. Nothing has been built or committed yet.
> Today: Fri Oct 2, 2026. Pilot write-up due: **Sat Oct 24, 2026** (about 3 weeks).

## 0. Decisions log

| Date | Decision |
|---|---|
| Oct 2 | Languages: all three (EN, TL, ZH). Tagalog written as natural **Taglish**; Mandarin in **Simplified** characters. |
| Oct 2 | Models: **Claude Sonnet 5.5** + **Gemini** (exact model TBD, to be checked against current lineup) + **qwen2.5:7b** (local, Ollama). |
| Oct 2 | Budget: hard cap **$20 for Claude, $20 for Gemini**, enforced by the runner. |
| Oct 2 | MAKE framing stays neutral ("can you just write it for me? i just need it to work."), with no "no explanation". |
| Oct 2 | Pages: publish the whole repo root, with an `index.html` at the root (existing workflow kept). |

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
│       ├── spec.en.md  spec.tl.md  spec.zh.md   # Clark writes/approves tl + zh
│       ├── test_spec.py       # hidden, scored tests
│       └── reference.py       # proves the tests are passable
├── prompts/framings.yaml      # MAKE / LEARN wrappers × {en, tl, zh}
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
| 2 | **You** write/verify Tagalog + Mandarin specs and framings | – | 5–7 h | Oct 8 |
| 3 | Model layer + runner + JSONL logging + cost meter; unit tests | 3 h | – | Oct 6 |
| 4 | Code extractor + Docker sandbox + checker; validate on references + deliberately broken code | 3 h | – | Oct 7 |
| 5 | **Dry run:** 2 tasks × all conditions; measure real tokens → updated cost estimate | 1 h | **approve cost** | Oct 8 |
| 6 | Full pilot run | ~1–2 h wall clock | – | Oct 9 |
| 7 | Codebook v1: you and I go through ~10 real responses together, then revise definitions | 1 h | 1.5 h | Oct 10 |
| 8 | **You** hand-code a stratified sample (≈ 25–30% of responses, balanced across model × framing × language) | 1 h (tooling) | 4–6 h | Oct 14 |
| 9 | (Optional) LLM pre-codes everything; κ vs your codes per code; decide what's reportable | 2 h | 30 min decide | Oct 15 |
| 10 | Analysis scripts + figures (descriptive; small-n, so no significance theatre) | 3 h | 1 h review | Oct 17 |
| 11 | Write-up draft (4–6 pp) → PDF | 3 h | 3–4 h edit | Oct 21 |
| 12 | Pages site + README final | 3 h | 1 h review | Oct 22 |
| – | Buffer | | | Oct 23–24 |

**Your total ≈ 17–24 hours over 3 weeks.** The critical path runs through *your* steps 2 and
8, so I'll make sure the pipeline is never what's holding them up.

## 4. Cost estimate (Claude API, before anything runs)

Pilot = 20 tasks × 2 framings × 3 languages (EN, TL, ZH; decided Oct 2) = **120 prompts per model**. Assumptions (deliberately
pessimistic): ~250 input tokens, and up to ~3,000 billed output tokens per call (visible answer
plus thinking, which can't be switched off on current Claude models). Current list prices:

| Model | $/M in · out | 120 calls (1 rep) | 360 calls (3 reps) |
|---|---|---|---|
| Claude Opus 5.5 | $4 · $20 | ~$7.50 | ~$22 |
| Claude Sonnet 5.5 | $2 · $10 | ~$3.70 | ~$11 |
| Claude Haiku 4.5 | $1 · $5 | ~$1.80 | ~$5.50 |
| Local Ollama model | free | $0 | $0 |

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
3. **Local model choice affects RQ3.** Qwen models are developed in China and are strong in
   Mandarin. Llama/Mistral are more English-centric. Either is defensible, but whichever we pick
   becomes part of the language story, and the write-up must name the confound.
4. **Correctness depends on the extractor.** If a response contains several code blocks, which
   one counts? Proposed rule: the last block that defines the required function. "No complete
   solution" is its own outcome, not "fail". (This matters for LEARN responses that scaffold.)
5. **Probes are unscored**, so models aren't penalised for reasonable choices on unspecified
   edge cases.

## 6. Open questions (beyond the three in chat)

- ~~Q1. Pilot languages~~ → **decided: all three (EN, TL, ZH).** Your step-2 load is now ~40 specs + 4 framings (≈ 5–7 h).
- **Q2. MAKE framing strength:** neutral ("can you just write it for me?") or explicitly
  code-only ("just the code, no explanation")?
- **Q3. Tagalog register:** formal Tagalog, or natural Taglish? (Taglish is more realistic for
  novices, but "language" then partly means "code-switching".) Mandarin: simplified or
  traditional characters?
- **Q4. Repetitions:** 3 per cell (recommended) or 1?
- **Q5. Effort level for Claude:** provider default, or a fixed value recorded explicitly?
- **Q6. Hand-coding sample size:** ~25–30% stratified, or all responses if the pilot is small
  enough?
