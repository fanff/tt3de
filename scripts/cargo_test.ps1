# Run the Python-independent Rust core tests.
# Usage (from repo root): powershell -ExecutionPolicy Bypass -File scripts/cargo_test.ps1 [cargo-args...]
# Example: powershell -ExecutionPolicy Bypass -File scripts/cargo_test.ps1 --lib
# From an existing PowerShell session: .\scripts\cargo_test.ps1 --lib
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path (Join-Path $root "crates/tt3de-core/Cargo.toml"))) {
    throw "cargo_test.ps1: expected crates/tt3de-core/Cargo.toml under $root"
}

& cargo test -p tt3de-core @args
