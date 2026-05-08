# Agent Guidelines for tt3de

## Build

This is a mixed Rust/Python project using [maturin](https://www.maturin.rs/).

- **Compile locally**: `uv run maturin develop` (dev profile) or `uv run maturin develop --profile release`
- **Rust check (all targets)**: `cargo check --all-targets` — use this to surface all warnings, including from tests and benchmarks.
- **Rust tests**: `cargo test`
- **Python tests**: `uv run pytest`
- **Regenerate TTSL opcodes**: `uv run tt3de-gen-opcodes`

## Platform Notes

- On Windows/PowerShell, redirect cargo stderr with: `cmd /c "cargo check --all-targets 2> output.txt"` (PowerShell `2>&1` piping mangles cargo output).

## Conventions

- Keep changes scoped; avoid unrelated refactors in the same edit.
- Run `cargo check --all-targets` after Rust edits to verify zero warnings.
- Run `uv run pytest` after changes that touch Python bindings.
