# -*- coding: utf-8 -*-
"""Guards the committed Criterion fixtures against demo shader drift.

``crates/tt3de-core/benches/ttsl/fixtures.rs`` holds bytecode compiled from the
TTSL demo shaders. Nothing in the Rust build recompiles it, so an edit to a demo
would leave the benchmark silently measuring stale bytecode.
"""
from __future__ import annotations

import importlib.util
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATOR = REPO_ROOT / "scripts" / "gen_ttsl_bench_fixtures.py"


def _load_generator() -> Any:
    spec = importlib.util.spec_from_file_location("gen_ttsl_bench_fixtures", GENERATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def generator() -> Any:
    return _load_generator()


def _committed_bytecode(source: str) -> Dict[str, List[int]]:
    """Pull ``name`` / ``bytecode`` pairs out of the generated Rust file."""
    out: Dict[str, List[int]] = {}
    pattern = re.compile(
        r'name:\s*"(?P<name>[^"]+)".*?bytecode:\s*&\[(?P<bytes>[^\]]*)\]',
        re.DOTALL,
    )
    for match in pattern.finditer(source):
        digits = [int(tok) for tok in re.findall(r"\d+", match.group("bytes"))]
        out[match.group("name")] = digits
    return out


def test_fixture_bytecode_matches_demo_shaders(generator: Any) -> None:
    committed = _committed_bytecode(generator.OUTPUT_PATH.read_text(encoding="utf-8"))
    assert committed, "no fixtures parsed out of the generated Rust file"

    for fixture in generator.build_fixtures():
        name = fixture.spec.name
        assert name in committed, f"{name} is missing from the committed fixtures"
        assert committed[name] == list(fixture.bytecode), (
            f"{name} bytecode changed; regenerate with "
            "`uv run --no-sync python scripts/gen_ttsl_bench_fixtures.py`"
        )


def test_generated_fixture_file_is_up_to_date(generator: Any) -> None:
    if shutil.which("rustfmt") is None:
        pytest.skip("rustfmt is required to reproduce the formatted fixture file")

    expected = generator.format_rust(generator.render_rust(generator.build_fixtures()))
    actual = generator.OUTPUT_PATH.read_text(encoding="utf-8")
    assert actual == expected, (
        "generated fixtures are stale; regenerate with "
        "`uv run --no-sync python scripts/gen_ttsl_bench_fixtures.py`"
    )


def test_ssa_json_matches_demo_shaders(generator: Any) -> None:
    for fixture in generator.build_fixtures():
        path = generator.SSA_DIR / f"{fixture.spec.name}.json"
        assert path.is_file(), f"{path.name} is missing from the committed SSA fixtures"
        assert path.read_text(encoding="utf-8") == fixture.ssa_json, (
            f"{fixture.spec.name} SSA snapshot changed; regenerate with "
            "`uv run --no-sync python scripts/gen_ttsl_bench_fixtures.py`"
        )
