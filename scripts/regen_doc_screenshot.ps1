# Regenerate source/_static/screenshots/triple_panel.svg without forcing a maturin reinstall.
# Uses `uv run --no-sync` so uv does not sync/rebuild the editable tt3de package first.
# Requires: extension already built (e.g. `uv run maturin develop`) and `uv` on PATH.
$ErrorActionPreference = 'Stop'
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $repoRoot
$script = Join-Path $PSScriptRoot 'dev_tt3de_screenshot.py'
uv run --no-sync python $script `
    -o source/_static/screenshots/triple_panel.svg `
    --width 132 --height 28
