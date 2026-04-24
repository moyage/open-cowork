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
"$PYTHON_BIN" -m unittest discover -s tests -v

echo "open-cowork smoke test passed."
