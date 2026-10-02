#!/usr/bin/env bash
# Fails if staged changes look like they contain secrets. Run by .githooks/pre-commit.
# Usage: scripts/check_secrets.sh            (checks staged changes)
#        scripts/check_secrets.sh --all      (checks every tracked file)
set -euo pipefail

status=0

# 1. No .env files (other than .env.example) may be staged or tracked.
if [[ "${1:-}" == "--all" ]]; then
  files=$(git ls-files)
else
  files=$(git diff --cached --name-only --diff-filter=ACMR)
fi
if echo "$files" | grep -E '(^|/)\.env($|\.)' | grep -v '\.env\.example$' ; then
  echo "BLOCKED: .env file is staged/tracked (above)." >&2
  status=1
fi

# 2. Key-shaped strings in content.
#    sk-ant-...      Anthropic keys
#    AIza...         Google API keys
#    AQ.<base64>     Google-style access keys
#    ghp_/github_pat GitHub tokens
#    KEY=<value> assignments with a non-empty value
patterns='sk-ant-[A-Za-z0-9_-]{10,}|AIza[0-9A-Za-z_-]{30,}|AQ\.[A-Za-z0-9_-]{30,}|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|(API_KEY|SECRET|TOKEN)[[:space:]]*=[[:space:]]*["'"'"']?[A-Za-z0-9_.-]{16,}'

if [[ "${1:-}" == "--all" ]]; then
  hits=$(git grep -nIE "$patterns" -- . ':!scripts/check_secrets.sh' || true)
else
  hits=$(git diff --cached -U0 -- . ':!scripts/check_secrets.sh' | grep -E '^\+' | grep -nE "$patterns" || true)
fi
if [[ -n "$hits" ]]; then
  # Print locations only, never the matched secret itself.
  echo "BLOCKED: possible secret in staged changes:" >&2
  echo "$hits" | cut -c1-60 | sed 's/=.*/=<redacted>/' >&2
  status=1
fi

if [[ $status -eq 0 ]]; then echo "check_secrets: OK"; fi
exit $status
