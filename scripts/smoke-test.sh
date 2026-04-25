#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON:-python3}"
OCW_BIN="${OCW_BIN:-"$ROOT_DIR/bin/ocw"}"

cd "$ROOT_DIR"

"$OCW_BIN" --help >/dev/null
"$OCW_BIN" version >/dev/null
"$OCW_BIN" adopt --target "$ROOT_DIR" --goal "Smoke test Agent-first adoption plan" --dry-run --format json >/dev/null
"$OCW_BIN" hygiene --format json >/dev/null
"$OCW_BIN" continuity --help >/dev/null

SMOKE_ROOT="$(mktemp -d)"
trap 'rm -rf "$SMOKE_ROOT"' EXIT
"$OCW_BIN" --root "$SMOKE_ROOT" init >/dev/null
"$OCW_BIN" --root "$SMOKE_ROOT" change create smoke-human-control --title "Smoke human control" >/dev/null
"$OCW_BIN" --root "$SMOKE_ROOT" change prepare smoke-human-control \
  --goal "Smoke test v0.2.8 enforceable human gates" \
  --scope-in "src/**" \
  --scope-in "tests/**" \
  --verify-command "python3 -m unittest discover -s tests" >/dev/null
"$OCW_BIN" --root "$SMOKE_ROOT" participants setup --profile personal --change-id smoke-human-control >/dev/null
"$OCW_BIN" --root "$SMOKE_ROOT" intent capture \
  --change-id smoke-human-control \
  --project-intent "Smoke test human-visible intent" \
  --requirement "Participants and intent are visible" \
  --acceptance "Step report can be generated" >/dev/null
"$OCW_BIN" --root "$SMOKE_ROOT" intent confirm \
  --change-id smoke-human-control \
  --confirmed-by human-sponsor >/dev/null
"$OCW_BIN" --root "$SMOKE_ROOT" step report --change-id smoke-human-control --step 5 >/dev/null
"$OCW_BIN" --root "$SMOKE_ROOT" step approve --change-id smoke-human-control --step 5 --approved-by human-sponsor >/dev/null
"$OCW_BIN" --root "$SMOKE_ROOT" run \
  --change-id smoke-human-control \
  --command-output "smoke command completed" \
  --test-output "smoke tests passed" \
  --modified "src/smoke.py" >/dev/null
"$OCW_BIN" --root "$SMOKE_ROOT" verify --change-id smoke-human-control >/dev/null
"$OCW_BIN" --root "$SMOKE_ROOT" review \
  --change-id smoke-human-control \
  --decision approve \
  --reviewer independent-reviewer \
  --rationale "Smoke lifecycle accepted" >/dev/null
"$OCW_BIN" --root "$SMOKE_ROOT" archive --change-id smoke-human-control >/dev/null
"$OCW_BIN" --root "$SMOKE_ROOT" status --sync-current-state >/dev/null

"$PYTHON_BIN" -m unittest discover -s tests -v

echo "open-cowork smoke test passed."
