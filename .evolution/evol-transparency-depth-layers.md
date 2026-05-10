# Evolution: Transparency, depth layers, and primitive ordering

```yaml
id: evol-transparency-depth-layers
status: proposed
created: 2026-05-11
authors: []
supersedes: []
superseded-by: ""
related:
  - source/low_level_api.rst  # Drawing Buffer + Depth layer resolve (canonical today)
  - src/raster/mod.rs         # raster_all: primitive iteration order
  - src/drawbuffer/           # DrawBuffer<K>, set_depth_content, material resolve
```

## Summary

Keep tt3de’s fixed two-layer per-terminal-cell depth stack as the default visibility and partial-transparency mechanism. Treat it explicitly as a small **K-buffer-style** resolve into a single `CanvasCell`, not as OpenGL’s one-depth-sample-plus-global-blend model. Document this consistently (including primitive submission order and material-defined compositing). Defer opaque/transparent material classification and an optional **second-pass** back-to-front transparent primitive sort until real scenes show artifacts the two-layer stack cannot handle.

## Motivation and context

Today the pipeline projects geometry into a `PrimitiveBuffer`, then `raster_all` walks primitives in buffer index order (`0..current_size`) with **no global sort** by depth or transparency. Visibility and limited transparency are handled **per cell** in `DrawBuffer<DEPTHCOUNT, f32>` (currently `DEPTHCOUNT == 2` via `DrawingBufferPy`): fragments are inserted nearest-first, deeper slots shift, overflow fragments drop, then `apply_material_on` shades **far-to-near** into one glyph plus front/back colors.

That differs from the common OpenGL recipe (opaque pass with depth write, then transparent pass sorted back-to-front with depth test on and depth write off). Users comparing to GL may misunderstand why ordering artifacts appear or why results depend on **material channel writes**, not a single blend equation.

This evolution captures a deliberate **scope and sequencing** decision: stay local and ASCII-centric first; add heavier global sorting only when justified.

## Goals

- **Clarity**: Readers of public docs understand (a) no primitive sort before rasterization, (b) two stored fragments per cell max, (c) resolve order and compositing are material-driven.
- **Stability**: No breaking change to default rendering; optional features are additive.
- **Future hook**: If implemented later, transparent pass design is **optional**, camera-depth-sorted, and clearly separated from the default path.
- **Honest performance framing**: Document expected cost ordering (opaque single-sample vs two-layer vs sorted transparent pass) as hypotheses, not benchmarks.

## Non-goals

- Replacing the two-layer model with full per-pixel A-buffer / depth peeling / “correct” order-independent transparency in the near term.
- Guaranteeing correct transparency for all intersecting transparent triangles (global sort is still approximate there).
- Changing `DEPTHCOUNT` in this evolution (remains a separate change with its own perf/test blast radius).

## User-visible functionality

- **After documentation-only work**: Library consumers and demo authors gain accurate mental models; behavior unchanged.
- **After optional transparent pass (future)**: Scenes that opt in could reduce some transparency ordering artifacts at the cost of sort + extra raster work; API surface TBD (e.g. render flag, material tags).
- **After material metadata (future)**: Materials could declare opaque vs transparent / alpha-blended to drive passes automatically; migration would be additive if defaults preserve current behavior.

## Technical approach

**Baseline (current architecture)**

- **Primitive order**: Determined by geometry buffer iteration and primitive buffer append order during projection/build—not reordered for visibility (see `build_primitives`, then `raster_all` sequential loop over `primitivbuffer.content`).
- **Per-cell stack**: `set_depth_content` maintains nearest-first layers; excess fragments discarded.
- **Resolve**: `apply_material_on` iterates layers far-to-near; each material writes subsets of `CanvasCell` channels (`StaticColor` toggles, `BaseTexture` alpha blend paths, etc.)—already described under **Depth layer resolve** in `source/low_level_api.rst`.

**Documentation alignment**

- Canonical technical description already lives in `source/low_level_api.rst` (**Depth layer resolve**). Close gaps by:
  - Adding a short, user-facing pointer in `source/high_level_api.rst` (or README “rendering model” blurb) linking to that section so high-level readers do not miss it.
  - Optionally noting explicitly in the **Primitive Buffer** subsection that rasterization consumes primitives **in buffer order** (no sort stage).

**Future: material metadata**

- Extend material definitions (Rust enum + Python bindings) with flags or categories: e.g. opaque vs transparent / alpha-blended. Pipeline uses flags only when a multi-pass path exists; default single pass unchanged.

**Future: optional transparent pass**

1. Raster opaque (or all non-transparent) primitives as today.
2. Collect transparent primitives (or indices) during build or mark in primitive buffer.
3. Sort transparent primitives **back-to-front** by a chosen depth key (e.g. centroid or nearest vertex in camera space—document approximation limits).
4. Second raster + resolve pass compositing on top of existing cell state (exact blend interaction with two-layer stack needs design if both apply).

**Alternatives considered**

- **Immediate GL-style sort for everything**: Rejected as default—`O(n log n)` sort, still wrong for intersections, conflicts with “small CPU scenes” simplicity unless needed.
- **Increase layer count globally**: Deferred—linear cost in per-cell work and shading; only if profiling shows two layers as the bottleneck *and* user value is clear.

## Usability and documentation

- Prefer **one canonical deep dive** (`source/low_level_api.rst`) plus **brief cross-links** from high-level docs / README so newcomers see “terminal cell stack + material writes” early.
- Demos that rely on transparency should mention ordering sensitivity (submission order + two-layer cap) in comments where non-obvious.
- If a transparent pass ships later: document sort key, limitations (intersections), and how it interacts with materials.

## Testability

- **Documentation**: No automated tests; reviewers verify accuracy against `DrawBuffer` and `apply_material_on` behavior.
- **Regression (existing)**: Extend or add tests under `tests/` if any doc-driven behavior is codified (e.g. two-layer drop policy, far-to-near resolve) — mirror patterns in `tests/tt3de/test_r_draw_buffer.py` and related Rust tests if present.
- **Future transparent pass**: Golden or coarse asserts on fragment ordering (unit tests on sort key), plus one e2e scene where back-to-front order visibly fixes a known artifact vs single-pass.
- **Edge cases to lock in**: Three overlapping transparent fragments at one cell (third drops); mixed materials where only some channels update; confirm primitive order dependence with a minimal scene.

## Complexity and scope

- **Doc + cross-links**: **S** — low risk, immediate value.
- **Material opaque/transparent metadata**: **M** — touches material enums, Python stubs, possibly prefabs.
- **Optional transparent pass**: **M/L** — primitive tagging/collection, sort, second raster path, interaction with two-layer resolve and materials.

Incremental shipping: document first; metadata second if multi-pass is planned; sort pass last behind an explicit opt-in.

## A priori performance analysis

**Hypothesized ranking (cheapest → expensive for typical ASCII-scale grids)**

1. **Single depth winner per cell, shade once**: Fewest branches and shader invocations; not the current default for transparency flexibility.
2. **Fixed two layers**: Extra insertion/shift work per covered fragment and up to two shades per cell—bounded by small `DEPTHCOUNT`, likely acceptable for modest triangle counts.
3. **Transparent primitive sort + extra pass**: `O(n log n)` CPU sort per frame (or per dirty region if incrementally optimized later), plus duplicate raster work for transparent subset; worsens with many transparent primitives.

**Validation ideas** (post-implementation): instrument frame time with dense transparent overlap; compare single-pass vs two-pass on stress demos; count `set_depth_content` hot-path hits under `perf` or Tracy if available.

## Risks and open questions

- **Sort key choice**: Centroid vs min depth vs max depth yields different artifacts; must be documented.
- **Interaction with two-layer stack**: Second pass might need rules for whether transparent fragments compete with opaque layers or replace resolve semantics.
- **Python API churn**: Opt-in flags must avoid surprising defaults for existing apps.
- **Correctness expectations**: Users may still expect GL-perfect transparency; docs must state non-goals clearly.

## Decision record

- **Status**: proposed
- **Resolution**: Adopt the two-layer K-buffer-like model as the ongoing default for visibility and lightweight transparency; prioritize making the model **discoverable and precise** in docs; treat OpenGL-style global transparent sorting and material classification as **optional later work** driven by demonstrated artifacts or product needs—not an immediate rewrite.

## References

- `source/index.rst` — CPU rasterization scope, small scenes
- `source/low_level_api.rst` — **Drawing Buffer**, **Depth layer resolve**, material modes
- `src/raster/mod.rs` — `raster_all` primitive iteration order
- `src/drawbuffer/` — `DrawBuffer`, depth insertion, material application
