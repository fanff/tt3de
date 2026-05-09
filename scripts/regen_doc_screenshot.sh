#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"
uv run --no-sync python scripts/dev_tt3de_screenshot.py \
  -o source/_static/screenshots/dual_panel.svg \
  --width 200 \
  --height 56
