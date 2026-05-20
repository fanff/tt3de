# -*- coding: utf-8 -*-
"""Render a compact Rich report from ``pytest-benchmark`` JSON for ``test_bench_material_apply``.

Designed for ~100-column terminals: narrow tables, short headers, small bar charts.

Typical workflow (repository root)::

    ./scripts/bench_material.sh

Manual equivalent::

    mkdir -p benchmarks
    PYTHONPATH=python uv run pytest \\
      benchs/r_code/test_bench_r_pix_shader.py::test_bench_material_apply \\
      --benchmark-only -q --benchmark-json=benchmarks/material_apply.json

    uv run --no-sync python scripts/dev_material_bench_report.py benchmarks/material_apply.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from bench_report_lib import ensure_repo_root, load_payload, report_material


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rich KPI report for test_bench_material_apply benchmark JSON.",
    )
    parser.add_argument(
        "json_path",
        nargs="?",
        default="benchmarks/material_apply.json",
        type=Path,
        help="pytest-benchmark --benchmark-json output (default: benchmarks/material_apply.json)",
    )
    parser.add_argument(
        "--max-width",
        type=int,
        default=100,
        metavar="N",
        help="cap console width for layout (default: 100)",
    )
    args = parser.parse_args()

    ensure_repo_root()
    payload = load_payload(args.json_path.resolve())
    report_material(payload, max_width=args.max_width)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(0)
