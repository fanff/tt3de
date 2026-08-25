#!/usr/bin/env bash
# Run the Python-independent Rust core tests.
# Usage (from repo root): bash scripts/cargo_test.sh [cargo-args...]
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

if [[ ! -f "$root/crates/tt3de-core/Cargo.toml" ]]; then
  echo "cargo_test.sh: expected crates/tt3de-core/Cargo.toml under $root" >&2
  exit 1
fi

exec cargo test -p tt3de-core "$@"
