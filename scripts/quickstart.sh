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

"$OCW_BIN" onboard --target "$TARGET_ROOT" --mode quickstart --yes
echo
echo "Agent-first adoption plan preview:"
"$OCW_BIN" --root "$TARGET_ROOT" adopt \
  --target "$TARGET_ROOT" \
  --goal "Apply open-cowork governance to this project iteration" \
  --dry-run
