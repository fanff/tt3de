---
id: evol-low-poly-uv-sphere-prefab
created: 2026-05-16
authors: [franc, codex]
supersedes: []
superseded-by: ""
related:
  - demos/3d/ttsl_normal_viewpos.py
  - python/tt3de/prefab3d.py
  - source/high_level_api.rst
  - .evolution/evol-ttsl-fragment-normal.md
---

## Summary

The `ttsl_normal_viewpos` demo proves TTSL **view-space varyings** (`tt_Normal`, `tt_ViewPos`) on a mesh where each triangle carries a **single flat (faceted) normal**—implemented today as demo-local `_low_poly_uv_sphere`. This evolution proposes moving that UV-mapped low-poly sphere generator into the public **3D prefab** layer (alongside `Prefab3D.unitary_cube` and friends), then refactoring the demo to call the shared API with unchanged geometry, winding, and UV layout.

## Motivation and context

- **Current behavior** — `demos/3d/ttsl_normal_viewpos.py` embeds ~40 lines of spherical grid math, triangle indexing, and per-corner UV assignment inside a private `_low_poly_uv_sphere` helper.
- The demo’s real story is **TTSL + varyings + lighting**; mesh construction noise competes for attention in the file readers open first.
- **Reference comparison** — `python/tt3de/prefab3d.py` already centralizes axis-aligned primitives (`unitary_triangle`, `unitary_square`, `unitary_cube`, …). A sphere fits the same mental model: “drop in a `TT3DPolygon` with documented topology.”
- **Semantics** — A **lat-long faceted** sphere (shared vertices, flat shading per triangle) matches common engine “low poly sphere” behavior and is what this demo relies on for interpretable `tt_Normal` gradients—not a smooth per-vertex normal sphere.
- **Reasoning** — Extracting the generator preserves raster/TTSL behavior (no renderer change) while making future 3D demos that need the same topology copy-paste safe.

## Goals

- Expose a reusable **low-poly UV sphere** constructor that returns `TT3DPolygon` with the same topology contract as today’s demo helper (**later API**).
- Document parameters (`radius`, `stacks`, `slices`), validity rules (`stacks >= 1`, `slices >= 3`), axis convention (Y-up, poles on ±Y), and UV range **[0, 1]** on each triangle (**docs+demo**).
- Refactor `demos/3d/ttsl_normal_viewpos.py` to use the shared API and delete `_low_poly_uv_sphere` (**docs+demo**).
- Keep the demo’s **visual and numeric behavior** equivalent (same radii, stack/slice counts, transforms, materials) for the initial slice (**docs+demo**).
- Add a short canonical snippet or cross-link under 3D prefab usage in `source/high_level_api.rst` (**docs-only**).

## Non-goals

- Changing Rust mesh rasterization, varying interpolation rules, or TTSL builtins.
- Adding **smooth** vertex-normal spheres, icospheres, or procedurally optimized LOD systems in this evolution.
- UV **seams** or cube-map style projections beyond the current lat-long strip layout.
- Replacing `TT3DPolygon` as the return type or introducing a new mesh asset type.

## User-visible functionality

- Demo and library users obtain a faceted sphere mesh from one documented call instead of duplicating trigonometry.
- `ttsl_normal_viewpos` stays the same showcase for `tt_Normal` / `tt_ViewPos`, with less boilerplate.
- Change is **additive** with a demo refactor: existing hand-built meshes are unaffected.

## Technical approach

- **Baseline (current architecture)** — Demo-local `_low_poly_uv_sphere(radius, stacks, slices)` builds `vertex_list`, `triangles`, and `uvmap` on `TT3DPolygon`, matching `Prefab3D` patterns used elsewhere.
- **Proposed change** — Add a static factory on `Prefab3D`, for example `Prefab3D.low_poly_uv_sphere(radius: float, stacks: int, slices: int) -> TT3DPolygon`, reusing the current algorithm verbatim (or moved line-for-line) so winding and UV corners stay identical.
- **Future / optional phases**
  1. Phase 1: `Prefab3D.low_poly_uv_sphere` + `ttsl_normal_viewpos` refactor + high-level doc note.
  2. Phase 2 (optional): adopt the same helper in any new 3D demo that needs a faceted sphere (e.g. lighting / normal debugging).
  3. Phase 3 (optional): consider a **cached** mesh for common `(stacks, slices)` tuples if multiple instances become hot in one process (likely unnecessary).
- **Alternatives considered**
  - Leave code demo-only: rejected; repeats discoverability issues already solved for cubes in `prefab3d.py`.
  - Implement in Rust first: deferred; Python-side `TT3DPolygon` population matches existing prefab style and avoids binding churn for a pure-CPU mesh list.
  - Generic “parametric surface” API: deferred; overkill until a second surface type needs the same abstraction.
- Affected subsystems:
  - `python/tt3de/prefab3d.py` (new method),
  - `demos/3d/ttsl_normal_viewpos.py`,
  - `source/high_level_api.rst` (short addition or link),
  - no TTSL opcode or compiler changes.

## Usability and documentation

- Mirror the docstring depth of `Prefab3D.unitary_cube` (axis, winding note if relevant, UV behavior).
- Clarify **faceted** shading: readers should understand why this mesh is appropriate for `tt_Normal` lighting demos versus a smooth sphere.
- Keep `ttsl_normal_viewpos` module docstring focused on varyings and shaders; the prefab becomes an import, not the story.

## Testability

- Pure-Python unit tests for `Prefab3D.low_poly_uv_sphere`:
  - vertex count `(stacks + 1) * (slices + 1)`,
  - triangle count `2 * stacks * slices`,
  - `uvmap` length matches `triangles`,
  - radius sanity: all vertices lie near `radius` from origin (within floating tolerance),
  - poles: top/bottom rings degenerate to single points (optional geometric assertions).
- Smoke run: `uv run python demos/3d/ttsl_normal_viewpos.py` after refactor.

## Complexity and scope

- Estimated size: **S** (single new factory + demo swap + small doc touch).
- Main risk: subtle **winding or UV** drift versus the demo’s current output; mitigate by copying implementation literally and locking tests to counts + optional golden checksum of first N vertex coordinates.
- Rollback: restore demo-local function if a regression appears; library method can remain unused.

## A priori performance analysis

- Work is **construction-time** only (small `O(stacks * slices)` lists); steady-state frame cost unchanged.
- No allocation hot path beyond one mesh build per sphere instance in typical demos.

## Risks and open questions

- **API naming** — `low_poly_uv_sphere` vs `faceted_uv_sphere` vs `latlong_uv_sphere`; pick one and stick to it in docs.
- **Default orientation** — must stay consistent with existing demo and with other `Prefab3D` primitives (Y-up convention).
- Open question: should `radius` default to `1.0` for parity with “unit” prefabs, or require an explicit radius to avoid silent scale mistakes? (Suggestion: require `radius` explicitly like the demo’s call sites, or default `1.0` with doc clarity.)

## Decision record

- **Resolution**: Pending — accepted direction is to consolidate the `ttsl_normal_viewpos` low-poly sphere into `Prefab3D` (or equivalent `python/tt3de/` prefab module) with equivalent geometry and tests, then slim the demo.

## References

- `python/tt3de/prefab3d.py`
- `demos/3d/ttsl_normal_viewpos.py`
- `source/high_level_api.rst`
- `.evolution/evol-ttsl-fragment-normal.md`
