#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_ROOT="${1:-}"
VENV_DIR="${OCW_VENV_DIR:-"$ROOT_DIR/.venv"}"

if [[ -z "$TARGET_ROOT" ]]; then
  cat <<USAGE
open-cowork quickstart

Usage:
  ./scripts/quickstart.sh /path/to/your-project

Optional:
  OCW_VENV_DIR=/tmp/open-cowork-venv ./scripts/quickstart.sh /path/to/your-project
USAGE
  exit 2
fi

mkdir -p "$TARGET_ROOT"
TARGET_ROOT="$(cd "$TARGET_ROOT" && pwd)"

echo "open-cowork quickstart"
echo "framework: $ROOT_DIR"
echo "target:    $TARGET_ROOT"
echo

"$ROOT_DIR/scripts/bootstrap.sh" >/tmp/open-cowork-bootstrap.log
OCW_BIN="$VENV_DIR/bin/ocw"

if [[ ! -x "$OCW_BIN" ]]; then
  echo "ocw command was not created at $OCW_BIN"
  echo "Bootstrap log: /tmp/open-cowork-bootstrap.log"
  exit 1
fi

echo "[1/3] Initialize governance structure"
"$OCW_BIN" --root "$TARGET_ROOT" init

echo
echo "[2/3] Show current status"
"$OCW_BIN" --root "$TARGET_ROOT" status

echo
echo "[3/3] Run session diagnosis"
"$OCW_BIN" --root "$TARGET_ROOT" diagnose-session

echo
echo "Quickstart complete."
echo
echo "Next commands you can run:"
echo "  $OCW_BIN --root \"$TARGET_ROOT\" change create personal-demo --title \"Personal domain pilot\""
echo "  $OCW_BIN --root \"$TARGET_ROOT\" status"
echo "  $OCW_BIN --root \"$TARGET_ROOT\" continuity digest --change-id personal-demo"
echo
echo "Read next:"
echo "  $ROOT_DIR/docs/getting-started.md"
