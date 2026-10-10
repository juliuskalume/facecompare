#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_PYTHON="$SCRIPT_DIR/.venv/bin/python"

if [ -x "$LOCAL_PYTHON" ]; then
  PYTHON="$LOCAL_PYTHON"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON="python3"
else
  PYTHON="python"
fi

exec "$PYTHON" -m uvicorn app.main:app --host 127.0.0.1 --port 8010
