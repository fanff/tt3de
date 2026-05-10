# Run `cargo test` with PyO3 pointed at the uv-managed interpreter.
# On Windows, prepends PATH so python3XY.dll resolves (avoids STATUS_DLL_NOT_FOUND / 0xc0000135).
# Usage (from repo root): powershell -ExecutionPolicy Bypass -File scripts/cargo_test.ps1 [cargo-args...]
# Example: powershell -ExecutionPolicy Bypass -File scripts/cargo_test.ps1 --lib
# From an existing PowerShell session: .\scripts\cargo_test.ps1 --lib
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path (Join-Path $root "pyproject.toml"))) {
    throw "cargo_test.ps1: expected pyproject.toml under $root"
}

$py = uv run python -c "import sys; print(sys.executable)"
$env:PYO3_PYTHON = $py
$base = uv run python -c "import sys; print(sys.base_prefix)"
$dlls = Join-Path $base "DLLs"
$prefix = "$(Split-Path $py -Parent);"
if (Test-Path $dlls) {
    $prefix += "$dlls;"
}
$prefix += "$base;"
$env:PATH = "$prefix$env:PATH"

& cargo test @args
