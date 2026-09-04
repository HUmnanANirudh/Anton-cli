#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$BIN_DIR"
chmod +x "$SCRIPT_DIR/anton.sh"

ln -sf "$SCRIPT_DIR/anton.sh" "$BIN_DIR/anton"

echo "Successfully linked Anton CLI to $BIN_DIR/anton"
echo ""
echo "You can now run Anton anywhere simply by typing:"
echo "  anton"
echo ""
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo "Note: Make sure $BIN_DIR is in your PATH. You can add it with:"
    echo '  export PATH="$HOME/.local/bin:$PATH"'
fi
