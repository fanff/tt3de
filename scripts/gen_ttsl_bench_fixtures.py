# -*- coding: utf-8 -*-
"""Generate the Rust bytecode fixtures used by the TTSL execution benchmark.

The TTSL front-end lives in Python while the interpreter and the Cranelift entry
point live in ``tt3de-core``. Compiling demo shaders at benchmark time would put
Python on the ``cargo bench`` path, so the bytecode and register seeds are
compiled here and emitted as a committed Rust file.

Shader sources are read from the demo modules themselves rather than copied, so
editing a demo shows up as a fixture diff instead of silently invalidating the
benchmark.

Run from the repository root::

    uv run --no-sync python scripts/gen_ttsl_bench_fixtures.py
"""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = REPO_ROOT / "crates" / "tt3de-core" / "benches" / "ttsl" / "fixtures.rs"

sys.path.insert(0, str(REPO_ROOT / "python"))

from pyglm import glm  # noqa: E402

from tt3de.ttsl.compiler import (  # noqa: E402
    GLOBAL_VAR_TT_FAR,
    GLOBAL_VAR_TT_NEAR,
    GLOBAL_VAR_TT_TIME,
    PIXELVAR_TT_FRAGCOORD,
    PIXELVAR_TT_FRAG_DEPTH,
    PIXELVAR_TT_NORMAL,
    PIXELVAR_TT_TEXCOORD0,
    PIXELVAR_TT_VIEW_POS,
    RegisterSettings,
    all_passes_compilation,
)


@dataclass(frozen=True)
class FixtureSpec:
    """One demo shader promoted to a benchmark fixture."""

    name: str
    demo: str
    source_attr: str
    entry: str
    summary: str
    globals_dict: Dict[str, Any] = field(default_factory=dict)
    #: Uniform seeds, resolved against module attributes when the value is a
    #: ``str`` naming one (glyph indices differ per glyph table build).
    uniforms: Dict[str, Any] = field(default_factory=dict)
    #: Per-pixel varyings a rasterized cell would carry into the shader.
    varyings: Dict[str, Any] = field(default_factory=dict)
    #: ``True`` when the shader calls ``tt_texture`` and needs a host texture env.
    needs_texture_env: bool = False


class ModuleAttr(str):
    """Marker: resolve this seed from an attribute of the demo module."""


FIXTURE_SPECS: Sequence[FixtureSpec] = (
    FixtureSpec(
        name="square_waves",
        demo="demos/2d/ttsl_square.py",
        source_attr="SHADER_SRC",
        entry="my_shader",
        summary="straight-line scalar math, three sin calls, no branches",
        globals_dict={GLOBAL_VAR_TT_TIME: float},
        uniforms={GLOBAL_VAR_TT_TIME: 3.25},
        varyings={PIXELVAR_TT_TEXCOORD0: glm.vec2(0.37, 0.61)},
    ),
    FixtureSpec(
        name="concentric_waves",
        demo="demos/2d/concentric_waves.py",
        source_attr="SHADER_SRC",
        entry="concentric_waves",
        summary="vec2/vec3 math with length, plus a four-way glyph branch chain",
        globals_dict={
            GLOBAL_VAR_TT_TIME: float,
            "u_g0": int,
            "u_g1": int,
            "u_g2": int,
            "u_g3": int,
        },
        uniforms={
            GLOBAL_VAR_TT_TIME: 3.25,
            "u_g0": ModuleAttr("GLYPH_TROUGH"),
            "u_g1": ModuleAttr("GLYPH_RIPPLE"),
            "u_g2": ModuleAttr("GLYPH_RING"),
            "u_g3": ModuleAttr("GLYPH_CREST"),
        },
        varyings={PIXELVAR_TT_TEXCOORD0: glm.vec2(0.37, 0.61)},
    ),
    FixtureSpec(
        name="depth_fog_glyph",
        demo="demos/3d/ttsl_fog_glyph_shadows.py",
        source_attr="SHADER_SRC",
        entry="depth_fog_glyph",
        summary="depth linearization with tt_Near/tt_Far uniforms and a branch chain",
        globals_dict={
            GLOBAL_VAR_TT_NEAR: float,
            GLOBAL_VAR_TT_FAR: float,
            "u_albedo": glm.vec3,
            "u_g0": int,
            "u_g1": int,
            "u_g2": int,
            "u_g3": int,
        },
        uniforms={
            GLOBAL_VAR_TT_NEAR: ModuleAttr("CAM_NEAR"),
            GLOBAL_VAR_TT_FAR: ModuleAttr("CAM_FAR"),
            "u_albedo": ModuleAttr("ALBEDO_RED_WALL"),
            "u_g0": ModuleAttr("GLYPH_D"),
            "u_g1": ModuleAttr("GLYPH_M2"),
            "u_g2": ModuleAttr("GLYPH_M3"),
            "u_g3": ModuleAttr("GLYPH_FULL"),
        },
        varyings={
            PIXELVAR_TT_FRAGCOORD: glm.vec2(0.37, 0.61),
            PIXELVAR_TT_FRAG_DEPTH: 0.82,
        },
    ),
    FixtureSpec(
        name="sphere_glyphs",
        demo="demos/3d/ttsl_normal_viewpos.py",
        source_attr="SHADER_SPHERE_GLYPHS_SRC",
        entry="sphere_glyphs",
        summary="vec3 varyings tt_Normal/tt_ViewPos with normalize, dot and clamp",
        globals_dict={
            "u_albedo": glm.vec3,
            "u_g_hash": int,
            "u_g_plus": int,
            "u_g_star": int,
            "u_g_dot": int,
        },
        uniforms={
            "u_albedo": ModuleAttr("ALBEDO_GLYPH_SPHERE"),
            "u_g_hash": ModuleAttr("GLYPH_HASH"),
            "u_g_plus": ModuleAttr("GLYPH_PLUS"),
            "u_g_star": ModuleAttr("GLYPH_STAR"),
            "u_g_dot": ModuleAttr("GLYPH_DOT"),
        },
        varyings={
            PIXELVAR_TT_FRAGCOORD: glm.vec2(0.37, 0.61),
            PIXELVAR_TT_NORMAL: glm.vec3(0.31, 0.62, -0.72),
            PIXELVAR_TT_VIEW_POS: glm.vec3(0.44, 0.18, 3.10),
        },
    ),
    FixtureSpec(
        name="texture_cube",
        demo="demos/3d/ttsl_texture_cube.py",
        source_attr="SHADER_SRC",
        entry="texshade",
        summary="tt_texture host callback, the one opcode class the JIT must call out for",
        varyings={PIXELVAR_TT_TEXCOORD0: glm.vec2(0.37, 0.61)},
        needs_texture_env=True,
    ),
)


def _load_demo_module(rel_path: str):
    path = REPO_ROOT / rel_path
    mod_name = "ttsl_bench_demo_" + path.stem
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import demo module {rel_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _resolve(value: Any, module: Any) -> Any:
    if isinstance(value, ModuleAttr):
        return getattr(module, str(value))
    return value


@dataclass
class CompiledFixture:
    spec: FixtureSpec
    bytecode: bytes
    registers: List[Dict[int, Any]]


def build_fixtures() -> List[CompiledFixture]:
    """Compile every demo shader and collect its bytecode plus seeded registers."""
    out: List[CompiledFixture] = []
    for spec in FIXTURE_SPECS:
        module = _load_demo_module(spec.demo)
        src = getattr(module, spec.source_attr)

        bytecode, reg_settings = all_passes_compilation(
            src, spec.entry, dict(spec.globals_dict)
        )
        _seed(reg_settings, spec.uniforms, module)
        _seed(reg_settings, spec.varyings, module)
        out.append(
            CompiledFixture(
                spec=spec,
                bytecode=bytecode,
                registers=reg_settings.get_register_list(),
            )
        )
    return out


def _seed(reg_settings: RegisterSettings, values: Dict[str, Any], module: Any) -> None:
    for name, raw in values.items():
        reg_settings.set_variable(name, _resolve(raw, module))


def _f32(value: Any) -> str:
    text = repr(float(value))
    return (
        text
        if ("." in text or "e" in text or "inf" in text or "nan" in text)
        else text + ".0"
    )


def _bool(value: Any) -> str:
    return "true" if value else "false"


def _i32(value: Any) -> str:
    return str(int(value))


def _scalar_entries(regs: Dict[int, Any], render) -> str:
    items = ", ".join(
        f"({reg}, {render(value)})" for reg, value in sorted(regs.items())
    )
    return f"&[{items}]"


def _vector_entries(regs: Dict[int, Any], width: int) -> str:
    items = []
    for reg, value in sorted(regs.items()):
        comps = ", ".join(_f32(value[i]) for i in range(width))
        items.append(f"({reg}, [{comps}])")
    return f"&[{', '.join(items)}]"


def _bytecode_literal(bytecode: bytes) -> str:
    rows = []
    for offset in range(0, len(bytecode), 6):
        instr = bytecode[offset : offset + 6]
        rows.append("            " + ", ".join(str(b) for b in instr) + ",")
    return "&[\n" + "\n".join(rows) + "\n        ]"


def render_rust(fixtures: Sequence[CompiledFixture]) -> str:
    lines: List[str] = [
        "// Generated by scripts/gen_ttsl_bench_fixtures.py. Do not edit manually.",
        "//",
        "// Bytecode and register seeds compiled from the TTSL demo shaders under demos/.",
        "",
        "/// A demo shader compiled to bytecode, with the register seeds a rendered cell",
        "/// would carry into the VM.",
        "pub struct TtslBenchFixture {",
        "    pub name: &'static str,",
        "    pub summary: &'static str,",
        "    pub demo: &'static str,",
        "    /// `true` when the shader calls `tt_texture` and needs a host texture env.",
        "    pub needs_texture_env: bool,",
        "    pub bytecode: &'static [u8],",
        "    pub seed_bool: &'static [(usize, bool)],",
        "    pub seed_f32: &'static [(usize, f32)],",
        "    pub seed_i32: &'static [(usize, i32)],",
        "    pub seed_v2: &'static [(usize, [f32; 2])],",
        "    pub seed_v3: &'static [(usize, [f32; 3])],",
        "    pub seed_v4: &'static [(usize, [f32; 4])],",
        "}",
        "",
        "pub const FIXTURES: &[TtslBenchFixture] = &[",
    ]

    for fixture in fixtures:
        regs_bool, regs_f32, regs_i32, regs_v2, regs_v3, regs_v4 = fixture.registers
        spec = fixture.spec
        lines.extend(
            [
                "    TtslBenchFixture {",
                f'        name: "{spec.name}",',
                f'        summary: "{spec.summary}",',
                f'        demo: "{spec.demo}",',
                f"        needs_texture_env: {_bool(spec.needs_texture_env)},",
                f"        bytecode: {_bytecode_literal(fixture.bytecode)},",
                f"        seed_bool: {_scalar_entries(regs_bool, _bool)},",
                f"        seed_f32: {_scalar_entries(regs_f32, _f32)},",
                f"        seed_i32: {_scalar_entries(regs_i32, _i32)},",
                f"        seed_v2: {_vector_entries(regs_v2, 2)},",
                f"        seed_v3: {_vector_entries(regs_v3, 3)},",
                f"        seed_v4: {_vector_entries(regs_v4, 4)},",
                "    },",
            ]
        )

    lines.extend(["];", ""])
    return "\n".join(lines)


def format_rust(source: str) -> str:
    """Run the rendered file through ``rustfmt`` so writes and checks agree."""
    try:
        done = subprocess.run(
            ["rustfmt", "--emit", "stdout", "--edition", "2021"],
            input=source,
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        print(
            "rustfmt not found on PATH; leaving generated file unformatted",
            file=sys.stderr,
        )
        return source
    # `--emit stdout` prefixes the body with a `<stdin>:` banner line.
    out = done.stdout
    marker = "\n"
    if out.startswith("<stdin>:"):
        out = out.split(marker, 1)[1]
    return out


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail instead of writing when the committed fixtures are stale",
    )
    args = parser.parse_args(argv)

    rendered = format_rust(render_rust(build_fixtures()))

    if args.check:
        current = (
            OUTPUT_PATH.read_text(encoding="utf-8") if OUTPUT_PATH.exists() else ""
        )
        if current != rendered:
            print(
                f"{OUTPUT_PATH.relative_to(REPO_ROOT)} is stale; "
                "run scripts/gen_ttsl_bench_fixtures.py",
                file=sys.stderr,
            )
            return 1
        return 0

    OUTPUT_PATH.write_text(rendered, encoding="utf-8")
    print(f"wrote {OUTPUT_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
