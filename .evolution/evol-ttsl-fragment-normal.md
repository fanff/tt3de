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

**Implementation order** — Work follows the numbered **Proposed phases** under [Technical approach](#technical-approach) (contract → compiler → Rust bridge → tests → docs).

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
- **Phased delivery** — Each goal above is attached to a **phase** below with explicit exit criteria; phases 2 and 3 may ship in one PR if desired (see [Proposed phases](#proposed-phases)).

## Non-goals

- **Changing the normal transform model** (inverse-transpose of MV in `triangle_3d.rs`) beyond clarifying docs.
- **Per-vertex smooth normal authoring** in `TriangleBuffer` / asset pipeline (separate content-pipeline evolution).
- **Tangent space / normal mapping**.
- **New TTSL opcodes** for normals — not required if the built-in is register-backed like other pixel varyings.

## User-visible functionality

- TTSL shaders may declare/use **`tt_Normal`** (implicit `vec3`, same pattern as `tt_FragCoord`): e.g. `n: vec3 = normalize(tt_Normal)` for lighting once `dot`/`normalize` are available (`source/ttsl.md` already lists those primitives as **Shipped**).
- **Breaking vs additive** — No new TTSL syntax beyond the implicit builtin. Shaders that **reference** `tt_Normal` get reads from the agreed `v3` slot. Once the material path **always** writes `PixInfo::normal` into `regs.v3[normal_v3_reg]`, the compiler **must** keep that index out of user temp allocation for that path (same pattern as UV slots `0`/`1`): expect the **first user `vec3` temp index to move from `2` to `3`** when this ships — document under Migration.
- **Migration** — Recompile TTSL sources after pulling; no Python scene API change unless new `ShaderPy.normal_v3_reg`-style knob is exposed for overrides (default should match compiler-fixed slot).

## Technical approach

### Baseline (current architecture)

| Piece | Role today |
|-------|------------|
| `PixInfo::normal` | Written in `DrawBuffer::set_depth_content` from raster (`src/drawbuffer/drawbuffer.rs`). |
| `Vertex::normal` | Interpolated in triangle raster (`src/raster/raster_triangle_tomato.rs`); for `triangle_3d`, three copies of triangle normal (`src/primitiv_building/triangle_3d.rs`). |
| `ShaderInputBinding` | `uv_v3_reg`/`uv1_v3_reg` = 0/1; no normal field (`src/material/shader_material.rs`). |
| Compiler | Reserves `v3` `{0,1}`; no `tt_Normal` in `PIXEL_VARIABLES_STR_TYPE` (`compiler.py`). |

### Coordination with `tt_ViewPos`

Shipping **`tt_Normal` at default `regs.v3[2]`** is a **hard prerequisite** for the default **`tt_ViewPos` at `regs.v3[3]`** layout assumed in [`.evolution/evol-ttsl-fragment-view-position.md`](evol-ttsl-fragment-view-position.md). Do not reorder those bank indices without updating both evolutions and the compiler/binding defaults together.

### Proposed phases

Phases are ordered to reduce **silent register mismatch** (compiler vs Rust). Phases **2** (compiler) and **3** (Rust bridge) may be combined in a **single PR** for an atomic ABI; keep them as separate headings for review and bisect.

#### Phase 1 — Contract freeze

**Intent** — Lock the public ABI slice that other evolutions depend on: builtin name, coordinate space, `v3` bank index, and reservation policy so [evol-ttsl-fragment-view-position](evol-ttsl-fragment-view-position.md) and tooling can assume stable defaults.

**Touch list** — This phase is documentation-only inside this evolution file (and optionally a short note in [evol-ttsl-fragment-view-position.md](evol-ttsl-fragment-view-position.md) if indices change — they should not after freeze).

**Exit criteria** — **Decision record** below lists frozen defaults; no open contradiction between Summary, Goals, and phases.

#### Phase 2 — Compiler + implicit builtin

**Intent** — Teach the compiler about `tt_Normal`, reserve `v3[2]` in `RegisterAllocatorPass` in lockstep with the frozen contract, and wire `RegisterSettings` / `ShaderPy` / `gather_shader_py_kwargs` if the project exposes overrides for other pixel registers (`frag_depth_f32_reg`, `line_coord_f32_reg`, etc.).

**Touch list**

- `python/tt3de/ttsl/compiler.py` — `PIXELVAR_*`, `PIXEL_VARIABLES` / typing maps, `RegisterAllocatorPass` reserved `v3` set, `RegisterSettings` / `ShaderPy` kwargs if applicable.

**Exit criteria** — `all_passes_compilation` on a minimal shader body that reads `tt_Normal` succeeds; disassembly / register plan shows **`v3` index `2`** for `tt_Normal` (or the frozen index from Phase 1). `cargo check --all-targets` and targeted `pytest` for compiler modules pass as required by [AGENTS.md](../AGENTS.md).

#### Phase 3 — Rust bridge

**Intent** — Extend `ShaderInputBinding` with `normal_v3_reg` (default **`2`**) and copy `pixinfo.normal` in `write_per_pixel_inputs_to_registers` so the VM sees raster data before `run_ttsl`.

**Touch list**

- `src/material/shader_material.rs` — `ShaderInputBinding`, `write_per_pixel_inputs_to_registers`, comments mirroring `compiler.py`.

**Exit criteria** — `cargo test` for the `shader_material` module (or crate subset) passes; manual or test assertion that `regs.v3[normal_v3_reg]` matches a crafted `PixInfo::normal` after the write helper runs.

#### Phase 4 — Tests

**Intent** — Lock ABI with regression coverage: material bridge, allocator behavior, and optional Python-level compile/e2e patterns used for `tt_FragPos` / `PrimitiveID`.

**Touch list**

- `src/material/shader_material.rs` — `#[cfg(test)]` as needed.
- `tests/tt3de/ttsl/` and/or `tests/tt3de/test_r_material.py` — wiring tests following existing `PixInfo` / `ShaderPy` patterns.

**Exit criteria** — New tests fail on intentional binding/index mismatch; **regression**: shaders that do not mention `tt_Normal` still compile and run, and user `vec3` temps do not overlap reserved `v3[2]` (see Decision record).

#### Phase 5 — User-facing docs + stubs

**Intent** — Ship canonical docs and optional `decorator.py` stub so `source/` matches runtime; document flat vs smooth, view-space, and `normalize(tt_Normal)` guidance once raster convention is verified.

**Touch list**

- `source/ttsl.md`, `source/ttsl_compiler.md` — built-in table + compiler notes.
- `python/tt3de/ttsl/decorator.py` — optional `tt_Normal` stub for type checkers / symmetry with other builtins.

**Exit criteria** — Docs rows match implementation; cross-links from [evol-lighting.md](evol-lighting.md) remain accurate.

### Alternatives considered

- **Opcode `TT_LOAD_NORMAL`** — Rejected for MVP: increases VM dispatch surface; redundant with register fill.
- **User uniform** — Rejected: normal varies per pixel; uniforms are wrong tool.

### Files likely touched (master list)

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

| Test idea | Phase |
|-----------|--------|
| **Rust unit test** — `PixInfo` with distinct `normal`, `write_per_pixel_inputs_to_registers` + readback of `v3[slot]` | 4 |
| **Python compile / e2e** — Shader referencing `tt_Normal`; disassembly / bank index | 4 |
| **Regression** — Shaders without `tt_Normal` compile; no user temp on reserved `v3[2]` | 4 (cross-phase with 2–3) |

## Complexity and scope

| Phase | Focus | Size | Risk |
|-------|--------|------|------|
| 1 | Contract freeze | S | Low |
| 2 | Compiler + builtin | S | Medium — register mismatch is silent garbage |
| 3 | Rust bridge | S | Low |
| 4 | Tests | S | Low |
| 5 | Docs + stubs | S | Low |

**Ships independently** — Yes, though lighting demos become meaningful only with `tt_ViewPos` and light data (see sibling evolution + `evol-lighting.md`).

**Rollback** — Remove built-in and bridge; revert reserved `v3` policy if no other consumer uses slot 2.

## A priori performance analysis

- **Hot path** — One extra `Vec3` write per shaded pixel (`write_per_pixel_inputs_to_registers`), negligible vs existing per-pixel writes.
- **Register pressure** — Consumes one `v3` index (256-wide bank; low impact).

## Risks and open questions

- **Normalization** — If raster passes **unnormalized** interpolated normals, document whether shaders should always `normalize(tt_Normal)` (likely yes). **Resolve in Phase 5** (docs + any engine comment), with a one-line note in Phase 1 if convention is known early.
- **Handedness / facing** — `tt_FrontFacing` exists; shaders may need `faceforward`-style logic later (`source/ttsl.md` lists `faceforward` as Planned).
- **Reserved `v3` indices** — Extending `{0,1}` → `{0,1,2}` moves the first user `vec3` temp slot; **Phase 4** must add allocator / regression coverage. Tied to **Phase 2** implementation.

## Decision record

- **Status**: draft (implementation landed; keep doc until release notes / changelog entry)
- **Builtin name**: **`tt_Normal`** (`vec3`), consistent with `evol-lighting.md` and `tt_` convention in `source/ttsl.md`.
- **Space**: Document as **view-space** to match current 3D primitive path (`triangle_3d` applies normal matrix then passes `normal_view`).
- **Register**: Default **`regs.v3[2]`** with `ShaderInputBinding::normal_v3_reg == 2` and compiler reservation of index **2** for the builtin (must stay aligned with Phase 2–3).
- **Reservation policy (frozen for MVP)** — Once the material path writes `PixInfo::normal` into `regs.v3[2]` every shaded pixel, the compiler **must** treat **`v3[2]` as engine-reserved** for that path (same idea as UV slots `0`/`1`), so user temporaries start at **`v3[3]`**. Shaders need not reference `tt_Normal` to be safe from overwrites.
- **Phase status**

| Phase | Status |
|-------|--------|
| 1 Contract freeze | Documented (this revision) |
| 2 Compiler | Implemented (`tt_Normal`, `v3[2]` pin, seeds) |
| 3 Rust bridge | Implemented (`normal_v3_reg`, per-pixel write) |
| 4 Tests | Implemented (Rust + Python) |
| 5 Docs + stubs | Implemented (`source/ttsl.md`, `ttsl_compiler.md`, `decorator.py`) |

- **Resolution**: *(fill when closing the evolution / shipping the feature)*

## References

- `.cursor/skills/tt3de-evol/template.md` — evolution skeleton (canonical template path in this repo)
- `src/drawbuffer/drawbuffer.rs` — `PixInfo`
- `src/primitiv_building/triangle_3d.rs` — per-triangle normal duplication
- `source/ttsl.md` — built-in inventory and math primitive availability
