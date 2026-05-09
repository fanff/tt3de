# -*- coding: utf-8 -*-
"""Benchmark canvas → Rich Segment export used by Textual (`DrawingBufferPy.to_textual_2`).

Example::

    PYTHONPATH=. uv run pytest tests/benchs/r_code/test_bench_to_textual.py --benchmark-only -v

Compare patterns at one size::

    PYTHONPATH=. uv run pytest tests/benchs/r_code/test_bench_to_textual.py --benchmark-only -v \\
      --benchmark-group-by=param:pattern

JSON export (includes pytest-benchmark ``datetime``; run enrich for ``timestamp`` / ``timestamp_unix``)::

    ./scripts/bench_to_textual.sh

    # equivalent manual steps:

    mkdir -p benchmarks
    PYTHONPATH=python uv run pytest tests/benchs/r_code/test_bench_to_textual.py \\
      --benchmark-only -q --benchmark-json=benchmarks/to_textual.json
    uv run python scripts/enrich_benchmark_json.py benchmarks/to_textual.json
"""

from __future__ import annotations

import pytest

from tt3de.tt3de import DrawingBufferPy

SIZES = (32, 128, 512)

# Inner iterations per pytest-benchmark invocation (reported time is for the whole batch).
ROUND_LOOPS = 20

PATTERNS = ("uniform", "gradient")


def _fill_canvas(db: DrawingBufferPy, rows: int, cols: int, pattern: str) -> None:
    if pattern == "uniform":
        front = (200, 120, 90, 255)
        back = (20, 24, 28, 255)
        for r in range(rows):
            for c in range(cols):
                db.set_canvas_cell(r, c, front, back, ord(" ") & 0xFF)
    elif pattern == "gradient":
        for r in range(rows):
            for c in range(cols):
                fr = (r * 7 + c * 3) & 255
                fg = (r * 11 + c * 5) & 255
                fb = (r * 13 + c * 17) & 255
                br = (255 - fr) & 255
                bg = (255 - fg) & 255
                bb = (255 - fb) & 255
                glyph = 32 + ((r + c) % 95)
                db.set_canvas_cell(r, c, (fr, fg, fb, 255), (br, bg, bb, 255), glyph)
    else:
        raise ValueError(f"unknown pattern: {pattern}")


def _loop_to_textual_2(db: DrawingBufferPy, cols: int, rows: int) -> None:
    for _ in range(ROUND_LOOPS):
        db.to_textual_2(min_x=0, max_x=cols, min_y=0, max_y=rows)


@pytest.mark.parametrize("n", SIZES)
@pytest.mark.parametrize("pattern", PATTERNS)
@pytest.mark.benchmark(group="to_textual_2")
def test_bench_to_textual_2(benchmark, n: int, pattern: str) -> None:
    db = DrawingBufferPy(n, n, material_parallel_threads=0)
    db.hard_clear(1.0)
    _fill_canvas(db, n, n, pattern)

    benchmark.extra_info["n"] = n
    benchmark.extra_info["pattern"] = pattern
    benchmark.extra_info["round_loops"] = ROUND_LOOPS

    benchmark(_loop_to_textual_2, db, n, n)
