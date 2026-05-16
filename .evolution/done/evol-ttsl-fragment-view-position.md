# Evolution: TTSL + engine — fragment position for lighting (`tt_ViewPos`)

```yaml
id: evol-ttsl-fragment-view-position
created: 2026-05-15
authors: []
supersedes: []
superseded-by: ""
related:
  - .evolution/evol-lighting.md
  - .evolution/evol-ttsl-fragment-normal.md
  - source/ttsl.md
  - source/ttsl_compiler.md
  - src/material/shader_material.rs
  - src/drawbuffer/drawbuffer.rs
  - src/raster/vertex.rs
  - src/primitiv_building/triangle_3d.rs
  - src/vertexbuffer/vertex_buffer.rs
```

## Summary

Introduce a TTSL implicit per-fragment built-in **`tt_ViewPos`: `vec3`** representing the **interpolated fragment position in view (eye) space**, suitable for point-light vectors, view-dependent effects, and the lighting reference shader in `evol-lighting.md`. Today **`tt_FragPos`** is documented and implemented as **cell-center NDC `vec2` only** (`source/ttsl.md`); `PixInfo` has no view-space position, and `Vertex` carries screen/clippable `pos` plus `normal`/`uv` but **no explicit view-space xyz varying** for interpolation. This evolution extends the primitive/raster bridge so the same perspective-correct interpolation machinery that feeds UVs and normals also feeds **view-space position**, then material application copies it into VM registers.

## Motivation and context

- **Current behavior** — `VertexBuffer::apply_mv` stores **`mv * vertex`** in the `mvp` slot (`get_calculated` in `src/vertexbuffer/vertex_buffer.rs`): for the 3D path this is **homogeneous view-space position** before projection. `triangle_3d.rs` then builds raster `Vertex` values with `pos` set from **projected screen coordinates and clip z/w** for coverage and depth — **not** directly carrying `get_calculated().xyz()` through to `PixInfo`. `PixInfo` exposes `frag_pos` as **NDC xy of the cell center** recomputed in `set_depth_content`, not the interpolated surface point in view space.

- **Problem** — Point lights need **`light_pos_view - frag_pos_view`**. Without `tt_ViewPos`, TTSL cannot express that in space consistent with planned `tt_lightPosition` (view space) in `evol-lighting.md`.

- **Reference comparison** — OpenGL varyings often include `highp vec3 vViewPos` from the vertex shader. tt3de should mirror that contract under a **`tt_`** name.

- **Interaction with depth** — `tt_FragDepth` remains the authoritative **stored depth test value** for the winning layer; `tt_ViewPos` is a **shading attribute** derived from geometry. Mismatches should only arise if depth is overridden or non-standard; document that both values come from the same raster sample for a given layer when possible.

- **Reasoning** — Prefer **interpolated view position** (varying) over reconstructing xyz from `tt_FragDepth` + inverse matrices inside TTSL (would require new matrix builtins and fragile numerics at terminal resolution).

## Goals

- **`tt_ViewPos`**: `vec3`, view-space, **per shaded fragment**, perspective-correct relative to the engine’s rasterization rules.
- **Raster / `PixInfo` plumbing** — Add a field (e.g. `view_pos: Vec3`) to `PixInfo`, set from raster at the same time as `normal` / UVs in `set_depth_content` (signature change on `DrawBuffer::set_depth_content` and Python `DrawingBufferPy.set_depth_content` — cascading but localized).
- **`Vertex` extension** — Carry per-vertex **view-space position** (either `Vec3` or `Vec4` with agreed w handling) through `primitivbuffer` / triangle submission so `raster_triangle_tomato` interpolates it like `normal` and `uv`.
- **`triangle_3d.rs`** — For each clipped triangle vertex, supply **per-corner view position** from `vertex_buffer.get_calculated(pa_idx)` (divide by `w` when using homogeneous `Vec4`) instead of only screen `pos`.
- **Compiler + `ShaderInputBinding`** — Add `PIXELVAR_TT_VIEW_POS` / `tt_ViewPos`, allocate a **`v3`** register (e.g. index **`3`** if `tt_Normal` occupies **`2`** — indices must be coordinated with `evol-ttsl-fragment-normal.md`).
- **Rust bridge** — `write_per_pixel_inputs_to_registers` writes `pixinfo.view_pos` into the chosen `v3` slot.
- **Docs** — `source/ttsl.md` row for `tt_ViewPos`; clarify distinction vs `tt_FragPos` (NDC `vec2` cell center).
- **Tests** — Raster + material integration: known triangle in view space → expected interpolated `tt_ViewPos` band in output colors.

## Non-goals

- **World-space or clip-space builtins** — Out of scope; document single **view** convention.
- **`tt_FragPos` breaking change** — Keep `vec2` NDC; do not overload its meaning.
- **Reconstructing view position from depth alone** as the primary path — optional future optimization only.
- **Stereo / multi-view** — Single active camera view.

## User-visible functionality

- Shaders use `let p: vec3 = tt_ViewPos` for lighting attenuation / view vectors alongside `tt_Normal` (sibling evolution).
- **Additive** — Existing shaders unchanged. New shaders pay one extra `v3` register and per-pixel write.
- **Python** — `set_depth_content` gains a `view_pos` argument **or** engine fills `PixInfo.view_pos` entirely from Rust raster (preferred: keep Python test helpers able to inject values mirroring Rust).

## Technical approach

### Baseline

| Piece | Today |
|-------|--------|
| `tt_FragPos` | `vec2` NDC cell center (`PixInfo.frag_pos`, `shader_material.rs` / `compiler.py`). |
| View-space verts | Available transiently in `VertexBuffer` after `apply_mv`; **not** threaded to `PixInfo`. |
| `Vertex` | `pos` (screen/clippable), `normal`, `uv` (`src/raster/vertex.rs`). |

### Proposed phases

1. **Geometry path** — Extend `Vertex` with `view_pos: Vec3` (name indicative). Update all `Vertex::new` / raster helpers (`raster_line`, `raster_rect`, defaults for non-3D primitives to `(0,0,0)` or sensible sentinel documented in `ttsl.md`).
2. **`triangle_3d` + clipping** — When emitting post-clip triangles, set each corner’s `view_pos` from transformed vertices; ensure perspective-correct interpolation weights match `uv` (divide-by-w pattern already used for `uv` storage).
3. **`set_depth_content`** — Accept interpolated `view_pos`, store in `PixInfo`.
4. **TTSL ABI** — Compiler + `ShaderInputBinding` + `write_per_pixel_inputs_to_registers`.
5. **Tests + docs** — Lock behavior; document interaction with `tt_FragDepth` and `tt_Near`/`tt_Far`.

### Alternatives considered

- **Builtin `vec4` view position with w** — Deferred; `vec3` matches lighting use cases with less shader churn.
- **Compute in TTSL from depth** — Rejected as primary path (missing inverse projection in TTSL today).

### Files likely touched

- `src/raster/vertex.rs`, `src/raster/raster_triangle_tomato.rs`, `src/raster/raster_line.rs`, `src/raster/raster_rect.rs`, `src/raster/mod.rs` (`set_depth_content` call sites)
- `src/primitiv_building/triangle_3d.rs`, possibly other primitive builders
- `src/drawbuffer/drawbuffer.rs`, `src/drawbuffer/mod.rs` (PyO3 `set_depth_content`)
- `src/material/shader_material.rs`
- `python/tt3de/ttsl/compiler.py`, `python/tt3de/ttsl/decorator.py`
- `source/ttsl.md`, `source/ttsl_compiler.md`
- `tests/tt3de/test_r_draw_buffer.py`, `tests/tt3de/ttsl/`, `tests/tt3de/test_r_material.py`

## Usability and documentation

- **`source/ttsl.md`** — Table entries: `tt_ViewPos` vs `tt_FragPos` (dimension, space, use cases).
- **`source/low_level_api.rst`** — Short note under pixel shader / `PixInfo` that view-space varyings exist for TTSL.
- Link from `.evolution/evol-lighting.md` reference shader snippets.

## Testability

- **Unit** — Barycentric midpoint of a triangle with known corner view positions → expected interpolated value (Rust raster test).
- **TTSL** — Shader returns `vec4(tt_ViewPos, 1.0)` mapped to color bands; compare to analytical values.
- **2D / rect path** — Defaults `(0,0,0)` or documented behavior; regression tests for “no crash + stable allocation”.

## Complexity and scope

| Area | Size | Risk |
|------|------|------|
| `Vertex` + all raster paths | M | Medium — many call sites |
| `set_depth_content` API | M | Medium — Python + Rust signature churn |
| Compiler + material bridge | S | Medium — must coordinate `v3` indices with `tt_Normal` |

**Dependency** — Coordinate register map with `evol-ttsl-fragment-normal.md` (`v3` bank layout).

## A priori performance analysis

- One extra `Vec3` interpolated attribute along triangle edges → incremental cost in raster setup; per-pixel one extra write to `PixInfo` and registers. Dominated by existing triangle iteration at terminal scales.

## Risks and open questions

- **W divide / perspective correction** — Must match UV convention (`Vertex` ops in `triangle_3d` multiply UV by `w` for perspective); view position interpolation must be **consistent** with documented behavior to avoid seams.
- **Clip / divide edge cases** — Clipped sub-triangles must carry correct interpolated `view_pos`.
- **Register pressure** — Two new `v3` builtins (`tt_Normal`, `tt_ViewPos`) consume two fixed indices; allocator must reserve both before user temps.

## Decision record

- **Builtin name**: **`tt_ViewPos`** (`vec3`), aligned with `evol-lighting.md` draft shader.
- **Space**: **View (eye) space**, consistent with directional/point light auto-transform in `evol-lighting.md`.
- **Coexistence with `tt_FragPos`**: No semantic overlap; docs must state both are available.
- **Resolution**: *(to be filled when closing)*

## References

- `.cursor/skills/tt3de-evol/template.md`
- `source/ttsl.md` — `tt_FragPos` semantics
- `src/vertexbuffer/vertex_buffer.rs` — `apply_mv` / `get_calculated`
- `.evolution/evol-ttsl-fragment-normal.md` — paired `v3` layout / lighting prerequisites
