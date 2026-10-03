# Who Gets Asked to Think?

**A Multilingual Audit of AI Coding Assistants' Explanations for Novice Programmers** (ThinkCheck)

> **Status: pilot, in progress (October 2026).** This is a small, machine-only audit of AI
> models. It is not a study of learners, and makes no claims about what students learn.

## Research questions

1. When novices ask AI coding assistants for help, how often do responses support
   **evaluative judgment** (explaining how the code works, stating assumptions and limits,
   flagging uncertainty, suggesting how to verify, inviting the learner to predict or modify)
   rather than just handing over code?
2. Does this differ between **"just make it"** and **"help me learn"** requests?
3. Does it differ by the **language** the novice writes in: English or Taglish (the everyday
   Tagalog–English mix many Filipino learners type in)?
4. Is the generated code **correct** against hidden automated tests?

## Method (pilot)

- 20 original beginner Python tasks, each with two framings and hidden unit tests.
- Prompts in English and Taglish. The author, a native speaker, wrote the Taglish prompts directly,
  with no machine translation.
- Chinoy (Filipino-Chinese) Mandarin and Hokkien are planned as a next step with native-speaker
  collaborators. They are not part of this pilot.
- Models: Claude Sonnet 5.5 (Anthropic API), a Gemini model (Google API), and qwen2.5:7b (local,
  via Ollama). Exact model IDs, parameters, and timestamps are logged for every call.
- Code is executed in an isolated sandbox (Docker, no network, time limits).
- Responses are coded with a codebook of evaluative-judgment features. Human codes are ground
  truth, and any LLM-assisted coding is reported with its agreement (Cohen's κ).

*Full method, reproduction steps, and limitations will be added as the pilot is built.*

## Setup

```bash
uv sync                       # installs pinned dependencies from uv.lock
cp .env.example .env          # then add your own API keys to .env (gitignored)
git config core.hooksPath .githooks   # enables the pre-commit secret check
```

## Builds on

- Prather et al. (2024). *The Widening Gap: The Benefits and Harms of Generative AI for Novice
  Programmers.* ICER '24. https://doi.org/10.1145/3632620.3671116
- Guo, P. J. (2018). *Non-Native English Speakers Learning Computer Programming: Barriers,
  Desires, and Design Opportunities.* CHI 2018.
