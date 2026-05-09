---
name: ttsl-implementation
description: Implements or changes Tiny Tiny Shader Language (TTSL) shaders, compiler, VM opcodes, or TTSL-related docs in tt3de. Use when writing TTSL source, editing python/tt3de/ttsl/, Rust TTSL VM/material paths, or when the user mentions TTSL, shader materials, bytecode, builtins (tt_FragCoord, tt_Time), or all_passes_compilation.
disable-model-invocation: true
---

# TTSL implementation

## Documentation map

Read these before changing behavior; they are the contract:

| Topic | File |
|-------|------|
| Builtins, uniforms, texture ABI, material bridge | [source/ttsl.md](../../../source/ttsl.md) |
| Compiler API, `globals_dict`, supported syntax | [source/ttsl_compiler.md](../../../source/ttsl_compiler.md) |
| Opcode numbers and operand types (generated) | [source/opcode_reference.md](../../../source/opcode_reference.md) |

## Authoring shader source

- **Return type**: `(front, back, glyph)` as `(vec3, vec3, int)`, matching VM `OP_RET`. Annotate `tuple[vec3, vec3, int]` (or `typing.Tuple[...]`) when typing the entry function.
- **Per-cell builtins** (`tt_FragCoord`, `tt_FragPos`, `tt_TexCoord0`, `tt_TexCoord1`, `tt_FrontFacing`, `tt_PrimitiveID`): known to the compiler; see `ttsl_compiler.md` for parameter declarations vs implicit slots.
- **Engine uniforms** (`tt_Time`, `tt_DeltaTime`, `tt_Frame`, `tt_Resolution`): include in `globals_dict` with the types documented in `ttsl.md` / `ttsl_compiler.md`; wire runtime setters and `ShaderPy.*_reg` to match `RegisterSettings` after `all_passes_compilation`.
- **Naming**: `tt_` + CamelCase, analogous to GLSL `gl_`.
- **Sampling**: only `tt_texture(index: int, coord: vec2) -> vec4` (and `tt_texelFetch` when implemented end-to-end—confirm opcode + compiler + tests). Use `tt_TexCoord*` for interpolated coords. Standalone Python `ttsl_run` does not bind textures; expect black or engine-defined fallback unless exercising through `Shader` + `TextureBuffer`.
- **Python next to shaders**: `from pyglm import glm` (same prelude convention as AGENTS.md).

## Compiler and bytecode

- **Pipeline entry**: `all_passes_compilation(src, func_name, globals_dict)` in `python/tt3de/ttsl/compiler.py`.
- **ISA / opcode definition changes**: edit `python/tt3de/ttsl/ttisa/low_level_def.py`, then run `make gen-opcodes` or `bash scripts/gen_opcodes.sh` (PowerShell script on Windows). That refreshes Rust opcodes, Python opcode tables, and `source/opcode_reference.md`.
- **Lowering gaps**: consult `source/ttsl_compiler.md` (supported features, typability in `type_of`, notes like partially wired helpers). Do not assume a name in `ttsl.md` primitives table compiles until verified in the compiler and tests.

## Adding a new opcode (end-to-end)

Work in roughly this order; adjust only when a step truly depends on another.

1. **Front end (Python compiler)** — Teach the compiler to recognize the new builtin, uniform, or primitive: parsing/AST, `type_of(...)`, and any surface rules so valid TTSL source type-checks before bytecode exists. Make sure a unittest is created to validate the front end pass

2. **Python ISA** — Add the opcode definition to `python/tt3de/ttsl/ttisa/low_level_def.py` (operand layout, typing contract as used by the encoder and docs).

3. **Rust VM** — Implement the opcode in the TTSL VM / interpreter (`src/ttsl/` and related call paths). **Before coding, confirm with the user** the intended strategy when execution needs data beyond current VM registers—e.g. geometry, primitive identity, raster context, textures, or other engine surfaces—so hooks stay consistent with materials and the render pipeline.

4. **Rust tests** — When the opcode has meaningful Rust-side semantics (pure VM behavior or small helpers), add or extend `cargo` tests so regressions show up without running the full Python stack.

5. **Regenerate and rebuild** — Run `make gen-opcodes` or `bash scripts/gen_opcodes.sh` (see AGENTS.md for Windows). Recompile Rust (`cargo check --all-targets`, `uv run maturin develop`, etc.) so generated opcode tables and the VM stay aligned.

6. **Compiler back end** — Implement lowering and bytecode emission (IR → encodings in `PassToByteCode` and related passes) so the front-end surface actually emits the new opcode. Make sure a unit test is create to validate the compiler back end

7. **Documenation Adjustment** -- After implementation, check the documention in the source/ folder and update the documentation to mention what is now implemented and tested

*Build hygiene*: Generated Rust/Python opcode artifacts track `low_level_def.py`. After any ISA edit, run `gen-opcodes` before relying on the new enum/constants in Rust; treat step 5 as the mandatory sync before merge even if an earlier local regen was needed to compile.

## Tests and doc updates

- Compiler or builtin changes: add focused cases under `tests/tt3de/ttsl/`; use material/apply paths when behavior crosses Rust.
- Any ABI or semantic change: update `source/ttsl.md` and/or `source/ttsl_compiler.md` in the same change; regenerate opcode docs when `low_level_def.py` moves.
