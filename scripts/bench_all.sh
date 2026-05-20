#!/usr/bin/env bash
# Run all engine benchmark suites (material, r_code, ttsl) sequentially.
# Usage (from anywhere): ./scripts/bench_all.sh
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"

for script in bench_material.sh bench_r_code.sh bench_ttsl.sh; do
  echo "==> ${script}" >&2
  bash "${root}/scripts/${script}"
done
