#!/usr/bin/env bash
# Run traindecade.com's regression tests locally, the same way CI does.
#
# WHY THIS EXISTS
#   These are standalone scripts, NOT pytest tests. Running `pytest tests/`
#   collects zero tests and silently "passes". This wrapper runs the real thing.
#
#   Also: the repo has no venv, and the system pythons are unusable here
#   (3.14 has no pytest; ga4-venv is activated in some shells). Pin one
#   interpreter so local runs match CI.
#
# USAGE
#   ./scripts/run_tests.sh              # build first, then test
#   ./scripts/run_tests.sh --no-build   # test existing ./public

set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO" || exit 1

PY="${TRAINDECADE_PYTHON:-/opt/homebrew/opt/python@3.13/bin/python3.13}"
if [ ! -x "$PY" ]; then
  PY="$(command -v python3)"
  echo "⚠️  pinned interpreter not found, falling back to $PY"
fi
echo "python: $PY ($("$PY" -V 2>&1))"

if [ "${1:-}" != "--no-build" ]; then
  echo "→ hugo build"
  hugo --gc --minify --baseURL "https://traindecade.com/" >/dev/null || {
    echo "❌ hugo build failed"; exit 1
  }
fi

if [ ! -d public ]; then
  echo "❌ ./public missing — build first (drop --no-build)"; exit 1
fi

fail=0

echo "→ bilingual invariants"
"$PY" tests/test_multilingual.py --public ./public || fail=1

echo "→ stray emphasis markers"
"$PY" tests/check_no_stray_emphasis.py --public ./public || fail=1

# Silent-JS regression: a broken outbound tracker produces no error and no
# data, which looks identical to "nobody clicked". Must run against a BUILD.
echo "→ GA4 outbound-click routing"
if command -v node >/dev/null 2>&1; then
  node scripts/test_outbound_tracking.js || fail=1
else
  echo "⚠️  node not found — SKIPPING outbound-click test (not a pass)"
fi

# Practitioner router maths harness (symptom->practitioner mapping).
if [ -f scripts/test_practitioner_router.js ]; then
  echo "→ practitioner router"
  node scripts/test_practitioner_router.js || fail=1
fi

# Non-blocking advisory check from the skill.
# Takes .md source files or --all (scans content/ + content-zh/). It does NOT
# accept a built-output directory — passing --public dir errors out.
SL="$HOME/.hermes/skills/software-development/traindecade/scripts/check_sentence_length.py"
if [ -f "$SL" ]; then
  echo "→ sentence length (advisory)"
  ( cd "$REPO" && "$PY" "$SL" --all 2>&1 | grep -E "^[0-9]+/[0-9]+ files" | tail -1 ) || true
fi

if [ "$fail" -eq 0 ]; then
  echo "✅ all tests passed"
else
  echo "❌ failures above"
fi
exit "$fail"
