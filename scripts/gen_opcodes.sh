#!/usr/bin/env bash
# Regenerate Rust/Python opcode outputs and Sphinx opcode_reference.md from low_level_def.py.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"

if [[ ! -f "${root}/pyproject.toml" ]]; then
  echo "gen_opcodes.sh: expected pyproject.toml under ${root}" >&2
  exit 1
fi

uv run --no-sync python python/tt3de/ttsl/ttisa/low_level_def.py
