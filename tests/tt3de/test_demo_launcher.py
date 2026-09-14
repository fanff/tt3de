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
    assert "ttsl_lighting.py" in stems
    assert "dust.py" in stems
    assert all(cat in ("2d", "3d") for cat, _ in pairs)


def test_list_demo_entries_does_not_import_scripts():
    """The menu must list files without executing demo modules (network, etc.)."""
    ns = _launcher_namespace()
    list_entries = ns["list_demo_entries"]
    repo = Path(__file__).resolve().parents[2]
    entries = list_entries(repo)
    assert len(entries) >= 8
    assert any(e.label == "3d/ttsl_lighting.py" for e in entries)
    assert all(e.view_cls is None for e in entries)
    assert all(e.widget_factory is None for e in entries)
    assert all(e.load_error is None for e in entries)


def test_dust_demo_import_has_no_network_side_effects(monkeypatch):
    """``demos/3d/dust.py`` used to download assets at import; that hung all.py."""
    ns = _launcher_namespace()
    load_demo_module = ns["load_demo_module"]
    repo = Path(__file__).resolve().parents[2]
    dust_path = repo / "demos" / "3d" / "dust.py"

    def _blocked_get(*_args, **_kwargs):
        raise AssertionError("dust.py import must not download assets")

    monkeypatch.setattr("requests.get", _blocked_get, raising=False)
    # If requests is imported only inside download_extract, patch the name
    # after a cheap import so a later call would still be caught.
    try:
        import requests

        monkeypatch.setattr(requests, "get", _blocked_get)
    except ImportError:
        pass

    mod = load_demo_module("3d", dust_path)
    assert hasattr(mod, "GLMTester")
    assert not (repo / "demos" / "3d" / "Dust").exists()


def test_build_demo_entries_all_resolve():
    ns = _launcher_namespace()
    build = ns["build_demo_entries"]
    repo = Path(__file__).resolve().parents[2]
    entries = build(repo)
    assert len(entries) >= 8
    ok = [e for e in entries if e.view_cls is not None or e.widget_factory is not None]
    assert len(ok) == len(entries), [
        (e.label, e.load_error)
        for e in entries
        if e.view_cls is None and e.widget_factory is None
    ]
    labels = {e.label for e in entries}
    assert "3d/ttsl_lighting.py" in labels
    lighting = next(e for e in entries if e.label == "3d/ttsl_lighting.py")
    assert lighting.view_cls is not None
    assert lighting.load_error is None
