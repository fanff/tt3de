# -*- coding: utf-8 -*-
"""Compact pytest-benchmark tables for tests collected under ``tests/benchs/r_code/``.

Loaded only when at least one test path under this directory is collected (including
other modules in this folder such as triangle raster). Slanted columns only; we do not
set ``--benchmark-group-by`` here because grouping by ``param:n`` would mis-handle
benchmarks that do not define ``n``.

Use ``--benchmark-group-by=param:n`` when running ``test_bench_r_pix_shader.py``
to compare serial vs parallel thread counts at each canvas size.
"""

from __future__ import annotations

import pytest


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config) -> None:
    opt = getattr(config, "option", None)
    if opt is None or not hasattr(opt, "benchmark_columns"):
        return
    opt.benchmark_columns = ["min", "max", "mean", "median", "ops"]
    opt.benchmark_sort = "mean"
    opt.benchmark_name = "short"
