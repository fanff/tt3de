<#
.SYNOPSIS
    Regenerate documentation screenshots (triple_panel.svg and triple_panel.png).

.DESCRIPTION
    Equivalent to running from the repository root:

        uv run tt3de-regen-doc-screenshot

    Uses --no-sync so uv does not sync the lockfile before running.

.EXAMPLE
    # From repo root:
    .\scripts\regen_doc_screenshot.ps1

.EXAMPLE
    # From anywhere (paths relative to this script):
    pwsh -File path\to\tt3de\scripts\regen_doc_screenshot.ps1
#>
$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $repoRoot

$conf = Join-Path $repoRoot 'source\conf.py'
if (-not (Test-Path -LiteralPath $conf)) {
    Write-Error "Expected Sphinx project at '$conf'. Run this script from the tt3de clone (scripts/ lives under the repo root)."
}

uv run --no-sync tt3de-regen-doc-screenshot
