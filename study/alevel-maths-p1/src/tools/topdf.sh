#!/bin/bash
# Usage: topdf.sh in.md out.pdf
set -e
D=$(dirname "$0")
TMP=$(mktemp --suffix=.html)
MD_BREAKS=${MD_BREAKS:-0} node "$D/build.js" "$1" "$TMP"
/opt/pw-browsers/chromium-1194/chrome-linux/chrome --headless=new --no-sandbox --disable-gpu --no-pdf-header-footer --print-to-pdf="$2" "file://$TMP" 2>/dev/null
rm -f "$TMP"
