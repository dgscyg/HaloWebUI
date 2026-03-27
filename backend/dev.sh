#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR" || exit 1
ROOT_DIR=$( cd -- "$SCRIPT_DIR/.." &> /dev/null && pwd )

PORT="${PORT:-8080}"
HOST="${HOST:-0.0.0.0}"

if [[ -n "${VIRTUAL_ENV:-}" && -x "${VIRTUAL_ENV}/bin/python" ]]; then
  PYTHON_BIN="${VIRTUAL_ENV}/bin/python"
elif [[ -x "${ROOT_DIR}/.venv/bin/python" ]]; then
  PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"
else
  PYTHON_BIN="python"
fi

if ! "$PYTHON_BIN" - <<'PY'
import importlib.util
import sys

required_modules = ("uvicorn", "sqlalchemy", "fastapi")
missing_modules = [name for name in required_modules if importlib.util.find_spec(name) is None]

if missing_modules:
    print(
        "Missing Python dependencies in interpreter:",
        sys.executable,
        "->",
        ", ".join(missing_modules),
        file=sys.stderr,
    )
    raise SystemExit(1)
PY
then
  echo "Hint: use the project virtualenv at ${ROOT_DIR}/.venv or install backend dependencies first." >&2
  exit 1
fi

exec "$PYTHON_BIN" -m uvicorn open_webui.main:app \
  --port "$PORT" \
  --host "$HOST" \
  --forwarded-allow-ips '*' \
  --reload
