# -*- coding: utf-8 -*-
"""Benchmark per-pixel material shading: serial vs Rayon (1/2/4/8 threads).

Each trial runs **1000** consecutive material passes on the same buffers (steady-state
frame loop), so Rayon scheduling overhead does not dominate tiny single-pass timings.

Compact tables (fewer columns, short names, sorted by mean) load automatically via
``tests/benchs/r_code/conftest.py`` when these tests are collected.

Example::

    uv run pytest tests/benchs/r_code/test_bench_r_pix_shader.py --benchmark-only -v

Export JSON and render a terminal KPI report (Rich; see README)::

    ./scripts/bench_material.sh

    # or (repository root):

    mkdir -p benchmarks
    PYTHONPATH=python uv run pytest tests/benchs/r_code/test_bench_r_pix_shader.py::test_bench_material_apply \\
      --benchmark-only -q --benchmark-json=benchmarks/material_apply.json
    uv run tt3de-material-bench-report benchmarks/material_apply.json

Group timings by canvas size (``n``)::

    uv run pytest tests/benchs/r_code/test_bench_r_pix_shader.py --benchmark-only -v \\
      --benchmark-group-by=param:n
"""
import pytest

from tt3de.tt3de import (
    DrawingBufferPy,
    MaterialBufferPy,
    PrimitiveBufferPy,
    TextureBufferPy,
    VertexBufferPy,
    apply_material_py,
    apply_material_py_parallel,
)

SIZES = (32, 128, 512)

# serial + parallel thread counts
PASS_CONFIG = (
    ("serial", None),
    ("parallel", 1),
    ("parallel", 2),
    ("parallel", 4),
    ("parallel", 8),
)
PASS_IDS = ("serial", "parallel_1t", "parallel_2t", "parallel_4t", "parallel_8t")

# Passes per benchmark invocation (reported times are for the whole batch).
FRAME_LOOPS = 100


def _material_frame_loop(mode: str, mb, tb, vb, pb, db) -> None:
    if mode == "serial":
        for _ in range(FRAME_LOOPS):
            apply_material_py(mb, tb, vb, pb, db)
    else:
        for _ in range(FRAME_LOOPS):
            apply_material_py_parallel(mb, tb, vb, pb, db)


@pytest.mark.parametrize("n", SIZES)
@pytest.mark.parametrize("mode,pool_threads", PASS_CONFIG, ids=PASS_IDS)
@pytest.mark.benchmark(group="material_shading")
def test_bench_material_apply(benchmark, n, mode, pool_threads):
    texture_buffer = TextureBufferPy(12)
    material_buffer = MaterialBufferPy()
    material_buffer.add_static((255, 90, 90, 255), (5, 10, 20, 255), 0)

    if mode == "serial":
        drawing_buffer = DrawingBufferPy(n, n, material_parallel_threads=0)
    else:
        assert pool_threads is not None
        drawing_buffer = DrawingBufferPy(n, n, material_parallel_threads=pool_threads)

    drawing_buffer.hard_clear(100.0)
    vertex_buffer = VertexBufferPy(32, 32, 32)
    primitive_buffer = PrimitiveBufferPy(3)

    benchmark.extra_info["n"] = n
    benchmark.extra_info["mode"] = mode
    benchmark.extra_info["pool_threads"] = pool_threads
    benchmark.extra_info["frame_loops"] = FRAME_LOOPS

    benchmark(
        _material_frame_loop,
        mode,
        material_buffer,
        texture_buffer,
        vertex_buffer,
        primitive_buffer,
        drawing_buffer,
    )
