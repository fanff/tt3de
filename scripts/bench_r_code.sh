#!/usr/bin/env bash
# Run triangle raster + Textual export benchmarks; print Rich summary.
# Usage (from anywhere): ./scripts/bench_r_code.sh
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"

if [[ ! -f "${root}/pyproject.toml" ]]; then
  echo "bench_r_code.sh: expected pyproject.toml under ${root}" >&2
  exit 1
fi
run_timestamp="$(date +%s)"
json_out="${root}/benchmarks/r_code_${run_timestamp}.json"
mkdir -p "${root}/benchmarks"
export PYTHONPATH="${root}/python"
uv run --no-sync pytest \
  benchs/r_code/test_bench_triangle_raster.py \
  benchs/r_code/test_bench_to_textual.py \
  --benchmark-only -q \
  --benchmark-json="${json_out}"

uv run --no-sync python scripts/enrich_benchmark_json.py "${json_out}"
uv run --no-sync python scripts/dev_bench_report.py r_code "${json_out}"
echo "Wrote ${json_out}"
