#!/usr/bin/env bash
# Run TTSL VM benchmarks and print Rich summary.
# Usage (from anywhere): ./scripts/bench_ttsl.sh
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"

if [[ ! -f "${root}/pyproject.toml" ]]; then
  echo "bench_ttsl.sh: expected pyproject.toml under ${root}" >&2
  exit 1
fi
run_timestamp="$(date +%s)"
json_out="${root}/benchmarks/ttsl_${run_timestamp}.json"
mkdir -p "${root}/benchmarks"
export PYTHONPATH="${root}/python"
uv run --no-sync pytest \
  benchs/ttsl/test_bench_ttsl.py \
  --benchmark-only -q \
  --benchmark-json="${json_out}"

uv run --no-sync python scripts/enrich_benchmark_json.py "${json_out}"
uv run --no-sync python scripts/dev_bench_report.py ttsl "${json_out}"
echo "Wrote ${json_out}"
