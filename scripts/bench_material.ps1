<#
.SYNOPSIS
    Run material-shading threading benchmark and print the Rich KPI report.

.DESCRIPTION
    Equivalent to README step 8: pytest exports JSON under benchmarks/, then
    tt3de-material-bench-report renders serial vs parallel KPIs for ~100-column terminals.

.EXAMPLE
    # From repo root:
    .\scripts\bench_material.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File C:\path\to\tt3de\scripts\bench_material.ps1
#>
$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $repoRoot

$proj = Join-Path $repoRoot 'pyproject.toml'
if (-not (Test-Path -LiteralPath $proj)) {
    Write-Error "Expected pyproject.toml at '$proj'. Run this script from the tt3de clone."
}

$benchDir = Join-Path $repoRoot 'benchmarks'
New-Item -ItemType Directory -Force -Path $benchDir | Out-Null

$jsonOut = Join-Path $benchDir 'material_apply.json'
$env:PYTHONPATH = 'python'

uv run --no-sync pytest `
    tests/benchs/r_code/test_bench_r_pix_shader.py::test_bench_material_apply `
    --benchmark-only -q `
    "--benchmark-json=$jsonOut"

uv run --no-sync tt3de-material-bench-report $jsonOut
