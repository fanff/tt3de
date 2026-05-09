# Regenerate Rust/Python opcode outputs and Sphinx opcode_reference.md from low_level_def.py.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path (Join-Path $root "pyproject.toml"))) {
    throw "gen_opcodes.ps1: expected pyproject.toml under $root"
}

uv run --no-sync python python/tt3de/ttsl/ttisa/low_level_def.py
