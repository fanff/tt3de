# Run TTSL benchmark tests (pytest-benchmark). Invoke from anywhere.
# Example: .\run_bench_ttsl.ps1
# Example: .\run_bench_ttsl.ps1 --benchmark-only
$ErrorActionPreference = 'Stop'
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
Set-Location $repoRoot
$testFile = Join-Path $PSScriptRoot 'test_bench_ttsl.py'
uv run pytest $testFile -v @args
