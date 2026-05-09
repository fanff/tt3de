#!/usr/bin/env bash
# Run material-shading threading benchmark and print the Rich KPI report.
# Usage (from anywhere): ./scripts/bench_material.sh
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"

if [[ ! -f "${root}/pyproject.toml" ]]; then
  echo "bench_material.sh: expected pyproject.toml under ${root}" >&2
  exit 1
fi

mkdir -p "${root}/benchmarks"
export PYTHONPATH="${root}/python"
uv run --no-sync pytest \
  tests/benchs/r_code/test_bench_r_pix_shader.py::test_bench_material_apply \
  --benchmark-only -q \
  --benchmark-json="${root}/benchmarks/material_apply.json"

uv run --no-sync tt3de-material-bench-report "${root}/benchmarks/material_apply.json"
