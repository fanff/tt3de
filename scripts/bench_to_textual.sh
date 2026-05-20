#!/usr/bin/env bash
# Deprecated: use scripts/bench_r_code.sh (includes Textual export + triangle raster).
set -euo pipefail
echo "bench_to_textual.sh: use scripts/bench_r_code.sh instead." >&2
exec "$(cd "$(dirname "$0")" && pwd)/bench_r_code.sh" "$@"
