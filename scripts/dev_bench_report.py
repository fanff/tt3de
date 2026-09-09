# -*- coding: utf-8 -*-
"""Rich terminal reports for pytest-benchmark JSON (material, r_code, ttsl suites)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from bench_report_lib import (
    ensure_repo_root,
    load_payload,
    report_material,
    report_r_code,
    report_ttsl,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rich KPI report for pytest-benchmark JSON artifacts.",
    )
    parser.add_argument(
        "suite",
        choices=("material", "r_code", "ttsl"),
        help="benchmark suite that produced the JSON",
    )
    parser.add_argument(
        "json_path",
        type=Path,
        help="pytest-benchmark --benchmark-json output",
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

    if args.suite == "material":
        report_material(payload, max_width=args.max_width)
    elif args.suite == "r_code":
        report_r_code(payload, max_width=args.max_width)
    else:
        report_ttsl(payload, max_width=args.max_width)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(0)
