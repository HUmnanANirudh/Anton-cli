#!/usr/bin/env bash

set -e

# Resolve the actual directory of this script, following symlinks
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
    DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
    SOURCE="$(readlink "$SOURCE")"
    [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"

# Ensure uv is available
UV_BIN="$(which uv 2>/dev/null || echo "$HOME/.local/bin/uv")"

if [ ! -x "$UV_BIN" ]; then
    echo "Error: 'uv' is not found. Please install uv (https://github.com/astral-sh/uv)." >&2
    exit 1
fi

# Ensure virtual environment exists in project directory
if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    (cd "$SCRIPT_DIR" && "$UV_BIN" venv && "$UV_BIN" pip install -e ".[dev]")
fi

# Run Anton CLI inside the project environment
exec "$UV_BIN" run --project "$SCRIPT_DIR" anton "$@"
