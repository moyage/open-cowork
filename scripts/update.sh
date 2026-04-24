#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKIP_GIT_PULL=0
BOOTSTRAP_ARGS=()

for arg in "$@"; do
  case "$arg" in
    --skip-git-pull)
      SKIP_GIT_PULL=1
      ;;
    --clean)
      BOOTSTRAP_ARGS+=("--clean")
      ;;
    *)
      echo "Unknown update option: $arg" >&2
      echo "Usage: ./scripts/update.sh [--skip-git-pull] [--clean]" >&2
      exit 2
      ;;
  esac
done

cd "$ROOT_DIR"

echo "open-cowork update"
echo "root: $ROOT_DIR"

if [[ "$SKIP_GIT_PULL" == "0" ]]; then
  git fetch --tags
  git pull --ff-only
else
  echo "git pull: skipped"
fi

"$ROOT_DIR/scripts/bootstrap.sh" "${BOOTSTRAP_ARGS[@]}"

VENV_DIR="${OCW_VENV_DIR:-"$ROOT_DIR/.venv"}"
"$VENV_DIR/bin/ocw" version
"$VENV_DIR/bin/open-cowork" version
"$ROOT_DIR/scripts/smoke-test.sh"

echo
echo "Update complete."
