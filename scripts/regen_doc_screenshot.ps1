# Regenerate Sphinx static dual-panel SVG (same as regen_doc_screenshot.sh).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

uv run --no-sync python scripts/dev_tt3de_screenshot.py `
    -o source/_static/screenshots/dual_panel.svg `
    --width 200 `
    --height 56
