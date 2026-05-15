# Evolution: TTSL + engine — interpolated fragment normal (`tt_Normal`)

```yaml
id: evol-ttsl-fragment-normal
status: draft
created: 2026-05-15
authors: []
supersedes: []
superseded-by: ""
related:
  - .evolution/evol-lighting.md
  - .evolution/evol-ttsl-fragment-view-position.md
  - source/ttsl.md
  - source/ttsl_compiler.md
  - src/material/shader_material.rs
  - src/drawbuffer/drawbuffer.rs
  - src/primitiv_building/triangle_3d.rs
```

## Summary

Expose the **interpolated geometric normal** already carried through rasterization in `PixInfo::normal` as a first-class TTSL per-fragment built-in named **`tt_Normal`** (`vec3`), aligned with `source/ttsl.md` naming (`tt_` prefix, GLSL-style role). Today the CPU rasterizer writes `normal` into `DrawBuffer::set_depth_content`, but **`ShaderMaterial::write_per_pixel_inputs_to_registers` never copies it into VM registers**, so TTSL shaders cannot read it. This evolution wires compiler register allocation, Rust `ShaderInputBinding`, and documentation so lighting and debug shaders can use the same normal the depth pass already stores.

## Motivation and context

- **Current behavior** — After rasterization, each depth layer’s `PixInfo<f32>` holds `uv`, `uv_1`, `frag_pos` (cell-center NDC `vec2`), **`normal: Vec3`**, IDs, facing, etc. (`src/drawbuffer/drawbuffer.rs`). `ShaderMaterial` copies UVs, `frag_pos`, depth, and optional facing/line/point fields into fixed register banks via `write_per_pixel_inputs_to_registers` (`src/material/shader_material.rs`), but **`normal` is omitted**. The TTSL compiler’s `RegisterAllocatorPass` pre-reserves `regs.v3[0]` and `regs.v3[1]` for the UV `vec2`→`vec3` bridge to match `ShaderInputBinding::default()` (`python/tt3de/ttsl/compiler.py` comments mirror `shader_material.rs`).

- **Problem** — Shaders that need a surface basis for lighting, fresnel, or debug visualization must guess from `tt_FragPos` (NDC `vec2` only) or uniforms; they cannot access the engine’s interpolated normal.

- **Reference comparison** — In GLSL, `in vec3` varyings (or legacy `gl_NormalMatrix` / transformed attributes) supply a per-fragment normal. tt3de already interpolates `Vertex::normal` across triangles in `raster_triangle_tomato` (same `Vertex` algebra as `uv`). The gap is purely **ABI + bridge**, not raster math.

- **Flat vs smooth caveat** — `triangle_3d.rs` builds each corner `Vertex` with the **same** `normal_view` copied from the **single** per-triangle object normal (`get_triangle` → `normal_vector`). Interpolation of three identical vectors is still that vector: **faceted (flat) shading** for typical 3D mesh submission. True smooth shading requires **per-vertex** normals in mesh data and passing distinct normals per corner (future mesh / builder work, out of scope for the register bridge itself). Document this limitation in `source/ttsl.md` so users do not assume Phong interpolation without asset support.

- **Reasoning** — Reuse `PixInfo::normal` and existing interpolation; avoid new opcodes (no `TT_NORMAL` fetch) unless the team prefers explicit VM ops over implicit loads — default proposal is **implicit built-in** like `tt_FragPos`, implemented as register fill before `run_ttsl`.

## Goals

- **`tt_Normal`**: Add `tt_Normal: vec3` to the TTSL implicit pixel variable set (`PIXEL_VARIABLES` / `PIXELVAR_*` in `compiler.py`), type-checked as view-space (or engine-defined) **unit direction** after transform where applicable.
- **Register contract** — Reserve a dedicated `v3` register index (e.g. **`2`**, after UV bridge slots `0` and `1`) in both `RegisterAllocatorPass` (extend the initial `allocated_registers[IRType.V3]` set) and `ShaderInputBinding` (new `normal_v3_reg: usize` or named field), documented in lockstep with `shader_material.rs` comments.
- **Rust bridge** — `write_per_pixel_inputs_to_registers` assigns `regs.v3[bind.normal_v3_reg] = pixinfo.normal` (exact field `PixInfo::normal`).
- **Docs** — Add a row to the built-ins table in `source/ttsl.md` (range/units: engine-defined, typically **view-space** non-normalized or normalized per raster path; state actual convention once chosen). Cross-link `source/ttsl_compiler.md` / decorator stubs if the repo keeps `decorator.py` aligned.
- **Tests** — Extend Rust `shader_material` tests and/or Python `tests/tt3de/ttsl/` patterns that already assert `tt_FragPos` / `PrimitiveID` wiring, to assert a non-default `PixInfo::normal` appears in the shaded result.

## Non-goals

- **Changing the normal transform model** (inverse-transpose of MV in `triangle_3d.rs`) beyond clarifying docs.
- **Per-vertex smooth normal authoring** in `TriangleBuffer` / asset pipeline (separate content-pipeline evolution).
- **Tangent space / normal mapping**.
- **New TTSL opcodes** for normals — not required if the built-in is register-backed like other pixel varyings.

## User-visible functionality

- TTSL shaders may declare/use **`tt_Normal`** (implicit `vec3`, same pattern as `tt_FragCoord`): e.g. `n: vec3 = normalize(tt_Normal)` for lighting once `dot`/`normalize` are available (`source/ttsl.md` already lists those primitives as **Shipped**).
- **Breaking vs additive** — Additive: shaders that do not reference `tt_Normal` keep identical register maps. Shaders that **do** reference `tt_Normal` get allocation of an additional `v3` bank index; hosts must compile with a `ShaderPy` / `RegisterSettings` path consistent with the new binding (same pattern as other pixel builtins).
- **Migration** — Recompile TTSL sources after pulling; no Python scene API change unless new `ShaderPy.normal_v3_reg`-style knob is exposed for overrides (default should match compiler-fixed slot).

## Technical approach

### Baseline (current architecture)

| Piece | Role today |
|-------|------------|
| `PixInfo::normal` | Written in `DrawBuffer::set_depth_content` from raster (`src/drawbuffer/drawbuffer.rs`). |
| `Vertex::normal` | Interpolated in triangle raster (`src/raster/raster_triangle_tomato.rs`); for `triangle_3d`, three copies of triangle normal (`src/primitiv_building/triangle_3d.rs`). |
| `ShaderInputBinding` | `uv_v3_reg`/`uv1_v3_reg` = 0/1; no normal field (`src/material/shader_material.rs`). |
| Compiler | Reserves `v3` `{0,1}`; no `tt_Normal` in `PIXEL_VARIABLES_STR_TYPE` (`compiler.py`). |

### Proposed change

1. **Compiler** — Add `PIXELVAR_TT_NORMAL = "tt_Normal"` → `IRType.V3`. Ensure allocation pins or picks the **same** index as Rust (recommended: pin to `2` by extending the reserved `v3` set to `{0,1,2}` when `tt_Normal` appears, **or** always reserve `2` for normal whenever any shader in the batch could share material — simplest is **always reserve slot 2** once the feature ships, mirroring how `i32` slots 1–3 shadow IDs).
2. **`ShaderInputBinding`** — Add `normal_v3_reg: usize` defaulting to `2` (must match compiler).
3. **`write_per_pixel_inputs_to_registers`** — Write `pixinfo.normal` into `regs.v3[normal_v3_reg]`.
4. **`RegisterSettings` / `ShaderPy`** — If the compiler exposes optional overrides for pixel regs, mirror the pattern used for `frag_depth_f32_reg` / `line_coord_f32_reg` in `compiler.py` (`gather_shader_py_kwargs`).

### Alternatives considered

- **Opcode `TT_LOAD_NORMAL`** — Rejected for MVP: increases VM dispatch surface; redundant with register fill.
- **User uniform** — Rejected: normal varies per pixel; uniforms are wrong tool.

### Files likely touched

- `python/tt3de/ttsl/compiler.py` — `PIXELVAR_*`, `RegisterAllocatorPass` reserved `v3` set, `RegisterSettings` / `ShaderPy` kwargs if applicable.
- `src/material/shader_material.rs` — `ShaderInputBinding`, `write_per_pixel_inputs_to_registers`, tests.
- `python/tt3de/ttsl/decorator.py` — optional stub `tt_Normal` for type checkers / symmetry with other builtins.
- `source/ttsl.md`, `source/ttsl_compiler.md` — built-in table + compiler notes.
- `tests/tt3de/ttsl/` or `tests/tt3de/test_r_material.py` — wiring tests following existing `PixInfo` / `ShaderPy` patterns.

## Usability and documentation

- **`source/ttsl.md`** — New row for `tt_Normal`: type `vec3`, document space (recommend **view-space**, matching how `triangle_3d` transforms normals) and flat-shading caveat for current `TriangleBuffer` normals.
- **`source/ttsl_compiler.md`** — Document implicit declaration / seed behavior (`vec3(0,0,1)` default vs `PixInfo::new()` default alignment).
- Cross-link `.evolution/evol-lighting.md` for consumers that need normals + lights together.

## Testability

- **Rust unit test** — Construct `PixInfo` with a distinct `normal`, run `write_per_pixel_inputs_to_registers` + minimal bytecode reading `v3[slot]`, assert color/glyph reflects input.
- **Python compile test** — Shader body referencing `tt_Normal` compiles; disassembly shows reads from expected register bank.
- **Regression** — Shaders without `tt_Normal` keep stable allocation (verify reserved-slot strategy does not steal user temps).

## Complexity and scope

| Area | Size | Risk |
|------|------|------|
| Compiler + binding alignment | S | Medium — register mismatch is silent garbage |
| Rust bridge | S | Low |
| Docs + tests | S | Low |

**Ships independently** — Yes, though lighting demos become meaningful only with `tt_ViewPos` and light data (see sibling evolution + `evol-lighting.md`).

**Rollback** — Remove built-in and bridge; revert reserved `v3` policy if no other consumer uses slot 2.

## A priori performance analysis

- **Hot path** — One extra `Vec3` write per shaded pixel (`write_per_pixel_inputs_to_registers`), negligible vs existing per-pixel writes.
- **Register pressure** — Consumes one `v3` index (256-wide bank; low impact).

## Risks and open questions

- **Normalization** — If raster passes **unnormalized** interpolated normals, document whether shaders should always `normalize(tt_Normal)` (likely yes).
- **Handedness / facing** — `tt_FrontFacing` exists; shaders may need `faceforward`-style logic later (`source/ttsl.md` lists `faceforward` as Planned).
- **Reserved `v3` indices** — Extending `{0,1}` → `{0,1,2}` changes the first free slot for user `vec3` temps; confirm allocator tests cover this.

## Decision record

- **Status**: draft
- **Builtin name**: **`tt_Normal`** (`vec3`), consistent with `evol-lighting.md` and `tt_` convention in `source/ttsl.md`.
- **Space**: Document as **view-space** to match current 3D primitive path (`triangle_3d` applies normal matrix then passes `normal_view`).
- **Register**: Default `regs.v3[2]` paired with compiler reservation (exact index subject to implementation review).
- **Resolution**: *(to be filled when closing)*

## References

- `.cursor/skills/tt3de-evol/template.md` — evolution skeleton (canonical template path in this repo)
- `src/drawbuffer/drawbuffer.rs` — `PixInfo`
- `src/primitiv_building/triangle_3d.rs` — per-triangle normal duplication
- `source/ttsl.md` — built-in inventory and math primitive availability
