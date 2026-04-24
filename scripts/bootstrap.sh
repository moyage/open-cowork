#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${OCW_VENV_DIR:-"$ROOT_DIR/.venv"}"
PYTHON_BIN="${PYTHON:-python3}"
CLEAN=0

for arg in "$@"; do
  case "$arg" in
    --clean)
      CLEAN=1
      ;;
    *)
      echo "Unknown bootstrap option: $arg" >&2
      echo "Usage: ./scripts/bootstrap.sh [--clean]" >&2
      exit 2
      ;;
  esac
done

echo "open-cowork bootstrap"
echo "root: $ROOT_DIR"
echo "venv: $VENV_DIR"

if [[ "$CLEAN" == "1" ]]; then
  if [[ -z "$VENV_DIR" || "$VENV_DIR" == "/" ]]; then
    echo "Refusing to clean unsafe venv path: $VENV_DIR" >&2
    exit 2
  fi
  echo "clean: removing existing venv before reinstall"
  rm -rf "$VENV_DIR"
fi

"$PYTHON_BIN" -m venv "$VENV_DIR"

if "$VENV_DIR/bin/python" - <<'PY'
from __future__ import annotations

import re
import subprocess
import sys


def version_tuple(value: str) -> tuple[int, ...]:
    match = re.search(r"(\d+(?:\.\d+)*)", value)
    if not match:
        return (0,)
    return tuple(int(part) for part in match.group(1).split("."))


pip_version = subprocess.check_output([sys.executable, "-m", "pip", "--version"], text=True)
try:
    import setuptools
    setuptools_version = setuptools.__version__
except Exception:
    setuptools_version = "0"

supports_editable_pyproject = (
    version_tuple(pip_version) >= (21, 3)
    and version_tuple(setuptools_version) >= (64,)
)
raise SystemExit(0 if supports_editable_pyproject else 1)
PY
then
  "$VENV_DIR/bin/python" -m pip install -e "$ROOT_DIR"
  echo "installed with pip editable mode"
else
  echo
  echo "local pip/setuptools does not support editable pyproject installs."
  echo "Creating a local ocw shim instead."
  cat > "$VENV_DIR/bin/ocw" <<SH
#!/usr/bin/env bash
export PYTHONPATH="$ROOT_DIR/src:\${PYTHONPATH:-}"
exec "$VENV_DIR/bin/python" "$ROOT_DIR/bin/ocw" "\$@"
SH
  chmod +x "$VENV_DIR/bin/ocw"
  cat > "$VENV_DIR/bin/open-cowork" <<SH
#!/usr/bin/env bash
exec "$VENV_DIR/bin/ocw" "\$@"
SH
  chmod +x "$VENV_DIR/bin/open-cowork"
fi

"$VENV_DIR/bin/ocw" --help >/dev/null
"$VENV_DIR/bin/open-cowork" --help >/dev/null

echo
echo "Bootstrap complete."
echo "Activate with:"
echo "  source \"$VENV_DIR/bin/activate\""
echo
echo "Verify with:"
echo "  ocw --help"
echo "  open-cowork --help"
echo "  ocw version"
echo "  ocw --root . init"
echo "  ocw --root . status"
echo "  ocw --root . adopt --target . --goal \"Describe the project iteration to govern\" --dry-run"
echo "  ocw --root . hygiene"
