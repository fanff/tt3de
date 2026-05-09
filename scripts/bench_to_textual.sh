#!/usr/bin/env bash
# Run canvas → Rich / Textual export benchmarks and write JSON (+ explicit timestamps).
#
# Output: benchmarks/to_textual.json
#   - Full pytest-benchmark payload (stats per test, machine_info, …)
#   - pytest-benchmark already sets top-level ``datetime`` (ISO-8601)
#   - scripts/enrich_benchmark_json.py adds ``timestamp`` and ``timestamp_unix``
#
# Usage (from anywhere): ./scripts/bench_to_textual.sh
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"

if [[ ! -f "${root}/pyproject.toml" ]]; then
  echo "bench_to_textual.sh: expected pyproject.toml under ${root}" >&2
  exit 1
fi

mkdir -p "${root}/benchmarks"
export PYTHONPATH="${root}/python"
run_timestamp="$(date --iso-8601=seconds)"
json_out="${root}/benchmarks/to_textual_${run_timestamp}.json"

uv run --no-sync pytest \
  tests/benchs/r_code/test_bench_to_textual.py \
  --benchmark-only -q \
  --benchmark-json="${json_out}"

uv run --no-sync python "${root}/scripts/enrich_benchmark_json.py" "${json_out}"

echo "Wrote ${json_out}"
