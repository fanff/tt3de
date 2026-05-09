# Run material-shading threading benchmark and print the Rich KPI report.
# Usage (from repo root): powershell -ExecutionPolicy Bypass -File scripts/bench_material.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path (Join-Path $root "pyproject.toml"))) {
    throw "bench_material.ps1: expected pyproject.toml under $root"
}

$runTimestamp = [long][Math]::Floor(([datetime]::UtcNow - [datetime]'1970-01-01').TotalSeconds)
$benchDir = Join-Path $root "benchmarks"
$jsonOut = Join-Path $benchDir "material_apply_${runTimestamp}.json"
New-Item -ItemType Directory -Force -Path $benchDir | Out-Null
$env:PYTHONPATH = Join-Path $root "python"

uv run --no-sync pytest `
    tests/benchs/r_code/test_bench_r_pix_shader.py::test_bench_material_apply `
    --benchmark-only -q `
    "--benchmark-json=$jsonOut"

uv run --no-sync python scripts/dev_material_bench_report.py $jsonOut
