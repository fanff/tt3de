#!/usr/bin/env bash
# Run `cargo test` with PyO3 pointed at the uv-managed interpreter.
# Usage (from repo root): bash scripts/cargo_test.sh [cargo-args...]
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

if [[ ! -f "$root/pyproject.toml" ]]; then
  echo "cargo_test.sh: expected pyproject.toml under $root" >&2
  exit 1
fi

export PYO3_PYTHON="$(uv run python -c 'import sys; print(sys.executable)')"
exec cargo test "$@"
