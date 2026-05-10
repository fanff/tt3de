# -*- coding: utf-8 -*-
"""Lightweight checks for ``demos/all.py`` discovery (no terminal UI)."""

from __future__ import annotations

import runpy
from pathlib import Path


def _launcher_namespace():
    repo = Path(__file__).resolve().parents[2]
    path = repo / "demos" / "all.py"
    return runpy.run_path(str(path), run_name="_tt3de_demo_launcher_test")


def test_discover_demo_paths_includes_known_scripts():
    ns = _launcher_namespace()
    discover = ns["discover_demo_paths"]
    repo = Path(__file__).resolve().parents[2]
    pairs = discover(repo)
    stems = {p.name for _, p in pairs}
    assert "standalone.py" in stems
    assert "ttsl_texture_cube.py" in stems
    assert all(cat in ("2d", "3d") for cat, _ in pairs)


def test_build_demo_entries_all_resolve():
    ns = _launcher_namespace()
    build = ns["build_demo_entries"]
    repo = Path(__file__).resolve().parents[2]
    entries = build(repo)
    assert len(entries) >= 8
    ok = [e for e in entries if e.view_cls is not None]
    assert len(ok) == len(entries), [
        (e.label, e.load_error) for e in entries if e.view_cls is None
    ]
