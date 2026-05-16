# Evolution: Rust render pipeline — unified frame entry + Rust-backed buffer arena

```yaml
id: evol-rust-render-context-unified-frame-buffers
created: 2026-05-16
authors: []
supersedes: []
superseded-by: ""
related:
  - source/low_level_api.rst
  - source/high_level_api.rst
  - python/tt3de/render_context_rust.py
  - python/tt3de/textual_standalone.py
  - python/tt3de/tt_2dnodes.py
  - python/tt3de/tt_3dnodes.py
  - src/lib.rs
  - src/primitiv_building/mod.rs
  - src/raster/mod.rs
  - .evolution/draft/evol-lighting.md
```

## Summary

Today `RustRenderContext` owns **many independent PyO3 buffer objects** (textures, materials, vertices, geometry, primitives, transforms, drawing). Indices tie them together (`material_id`, texture slots, geometry ids). Each frame, `TT3DViewStandAlone.update_frame` runs user hooks then `RustRenderContext.render`, which in turn issues **multiple top-level PyO3 calls** (`build_primitives_py`, `raster_all_py`, `apply_material_py` / parallel variants) that each re-acquire Rust references to overlapping buffer sets (`src/primitiv_building/mod.rs`, `src/raster/mod.rs`, `src/lib.rs`). This evolution targets **two coupled improvements in one narrative**: (1) **one native-orchestrated frame pass** (or a minimal sequence) so the hot path crosses the Python boundary far fewer times per frame, and (2) **Rust-centralized buffer storage and mutation** so geometry/material/raster inputs share **better allocation locality** and fewer disjoint heap regions—**without** moving the **scene graph** (parent/child nodes, `insert_in` / `sync_in_context` policy) into Rust.

## Motivation and context

- **Current behavior** — `RustRenderContext.__init__` constructs separate `*BufferPy` handles (`python/tt3de/render_context_rust.py`). `render()` sets camera matrices on `TransformPackPy`, clears `PrimitiveBufferPy`, runs `process_dirty()` (Python walks `roots_nodes` and calls `sync_in_context`), then calls `build_primitives_py(geometry, vertex, transform, drawing, primitive)`, opaque `raster_all_py`, opaque `apply_material_py` (or parallel), transparent `raster_all_py`, transparent `apply_material_py`. `TT3DViewStandAlone.update_frame` wraps that with `update_step`, `before_render_step`, `clear_canvas`, `post_render_step` (`python/tt3de/textual_standalone.py`). `render_lines` may skip `update_frame` when throttled but still calls `to_textual_2`.

- **Problem** — (a) **FFI churn**: each `*_py` entry is a full boundary crossing with argument marshaling and borrow checks, even though the buffers belong to one logical context. (b) **Memory layout**: many Python-visible objects wrap separate Rust allocations; index indirection across buffers is inherent to the engine model but **backing storage fragmentation** and cache-unfriendly access patterns are not mandatory forever.

- **Reference comparison** — Game/graphics engines often keep a **render device or frame context** that owns transient GPU resources and records one **command buffer** or **pass list** per frame. tt3de is CPU-only, but the same idea applies: **one context object** should be able to **execute the full raster pipeline** internally once inputs are stable.

- **Reasoning** — Batching FFI and co-locating Rust buffers are **orthogonal but synergistic**: a single `render_frame_inner` can take `&mut` on all arena slices without re-exporting seven handles through Python each sub-step. Keeping the **scene graph in Python** preserves rapid iteration, Textual integration, and existing `TT2DNode` / `TT3DNode` APIs; only the **sink buffers** and **pipeline orchestration** move toward Rust-centric design.

## Goals

- **Unified native frame execution** — Expose (or migrate to) a **single PyO3 entry** (or a **fixed tiny sequence**, e.g. clear + render + optional stats) that runs **build → raster opaque → shade opaque → raster transparent → shade transparent** inside Rust without Python dispatch between those steps. `RustRenderContext.render` becomes a thin wrapper or delegates to that entry.
- **Rust-backed buffer arena** — Where practical, **co-locate or sub-allocate** the Rust sides of geometry, vertex, primitive, transform, and draw-related storage so hot paths see **fewer distinct allocations** and better sequential access for typical small scenes (dozens of triangles, modest object counts per `source/index.rst`). Exact layout (SoA vs hybrid) is an implementation choice documented in the decision record.
- **Stable public indices** — Preserve **material_id**, geometry slot semantics, and documented reserved slots (e.g. geometry index `0`, material `0` void) unless a migration is explicitly versioned (`source/low_level_api.rst`).
- **Python API continuity** — `RustRenderContext` remains the user-facing aggregate; demos may still assign `self.rc.texture_buffer` / `material_buffer` for ergonomics **or** gain accessors that forward to the same Rust arena—**no requirement** to move node classes to Rust.
- **Observability** — Preserve or improve the ability to time sub-stages (either Rust-returned timings or optional hooks) so `FrameTimings` / debug tooling do not regress.

## Non-goals

- **Scene graph in Rust** — No Rust `TT3DNode` tree, no Rust-owned parenting, no replacement of `insert_in` / `sync_in_context` traversal in this evolution. Python remains the authority for **what** gets written into buffers; this work improves **where** those writes land and **how** the frame pass runs.
- **Changing raster or blend semantics** — Depth two-pass model, `pass_filter` behavior, and material rules stay as documented unless a bugfix is unavoidable (then call it out explicitly).
- **TTSL / opcode changes** — Not required for layout or FFI batching; cross-link only if register ABI touches material apply internals.

## User-visible functionality

- **Additive default** — Prefer a path where existing demos **keep working** with `RustRenderContext` construction and `append_root` unchanged.
- **Optional stricter API** — New helpers (e.g. `rc.render_frame(camera)` implemented as native orchestration) may deprecate direct Python calls to `build_primitives_py` from user code if those were ever public; if they remain public for tests, document **preferred** vs **low-level** APIs in `source/high_level_api.rst` / `source/low_level_api.rst`.
- **Resize** — `update_wh` / drawing buffer recreation must remain correct; arena growth policy should avoid O(n) full copies every resize if possible (document trade-offs).

## Technical approach

### Baseline (current architecture)

| Layer | Facts today |
|-------|-------------|
| Python context | `RustRenderContext` holds separate `*Py` buffer objects and `roots_nodes`; `render()` chains multiple `*_py` exports. |
| PyO3 surface | `build_primitives_py`, `raster_all_py`, `apply_material_py`, `apply_material_py_parallel` registered in `src/lib.rs`; signatures pass overlapping buffers (`src/primitiv_building/mod.rs`). |
| Frame driver | `TT3DViewStandAlone.update_frame` → `process_dirty` (Python) → `render()` pipeline → `to_textual_2` for Textual strips. |

### Proposed change (combined scope)

1. **Native `RenderContext` (name TBD)** — Introduce a Rust struct that **owns** (or uniquely borrows for the frame) all buffers needed for `build_primitives` → `raster_all` → `apply_material` paths. The existing `*BufferPy` types either **wrap a handle into that arena** or become **facades** that read/write through stable offsets (indices unchanged at the Python semantic layer).

2. **Single orchestration function** — Implement something like `render_context_run_frame_py(...)` **or** a method on one Py class that **does not return to Python** between internal phases except for errors. Reuse existing `build_primitives`, `raster_all`, `apply_material_on*` implementations by **inlining the call sequence** in Rust to avoid duplicate logic.

3. **`RustRenderContext.render` migration** — After `process_dirty()` (still Python), call the unified native entry with **camera matrices** (or a small packed `CameraFrame` POD crossing the boundary once). Transparent pass continues to use serial `apply_material_py` behavior today unless parallel transparent shading is separately justified.

4. **Buffer mutation in Rust** — Geometry append, primitive clear/fill, transform pack updates, and draw buffer clears **may move** so the hot mutations hit **contiguous or arena-backed** storage. Python `sync_in_context` still **decides** content but may call **narrower** PyO3 methods (bulk writes, `extend_from_slice`-style) to minimize per-element overhead.

### Rust buffer arena — what it means (and what it is not)

- **Definition (for this evolution)** — One **Rust-owned allocation region** (or a small number of regions: e.g. “static scene buffers” vs “per-frame scratch”) that backs the **engine sink data** the raster pipeline reads: geometry slots, vertex/UV/triangle data, primitive stream, transform pack, and optionally material/texture **payload** blobs. Indices (`material_id`, geometry id, texture slot) remain **logical**; they become **offsets or handles** into arena slices instead of each buffer being a separate `Vec` behind a separate PyO3 type.

- **Not in scope for the word “arena”** — A general-purpose global allocator, replacing `Vec` growth semantics everywhere, or packing **Python** objects. The scene graph stays Python; only the **Rust side** of the buffer story is denser.

- **Coupling to unified frame entry** — The main payoff is **borrow + pointer locality inside Rust**: one `render_frame_inner(&mut Arena)` can mutably access all participating slices without juggling seven independent `PyRefMut` chains. **Cache locality** is a **secondary** hypothesis: tt3de scenes are small, but separate `Vec` headers and heap blocks still add pointer-chasing and allocator traffic on resize/growth.

### Existing high-level interface — can it stay?

**Yes — by design.** The public story in `source/high_level_api.rst` (`TT3DViewStandAlone`, `self.rc`, `append_root`, `MaterialPerfab.rust_set_0()`, `material_buffer.add_*`, geometry on nodes) should remain **source-compatible** for demos.

| Public surface | Binding strategy |
|----------------|------------------|
| `RustRenderContext` | Still the aggregate constructed by `TT3DViewStandAlone`; holds (or owns) a single Rust arena / native context pointer. |
| `self.rc.texture_buffer`, `material_buffer`, … | Keep as **attributes on the same object** (`TextureBufferPy`, …) implemented as **thin facades**: methods forward to the shared arena (same logical indices, same behavior). |
| `sync_in_context` / `insert_in` | Unchanged Python signatures taking `RustRenderContext`; internally they call the same PyO3 methods, which mutate **arena sub-ranges** instead of disjoint `Vec`s. |
| `build_primitives_py` etc. | May remain for tests/low-level tools, or become thin wrappers that delegate into the arena-backed implementation. |

**Compatibility caveats to document** — `id(obj)` equality or identity of buffer objects across `update_wh` / arena realloc is **not** a guaranteed public contract unless explicitly tested; demos should rely on **`self.rc`** and attributes, not on “is this the same `GeometryBufferPy` instance as before resize.”

### Alternatives considered

- **Python-only batching** — Concatenate calls in Python with no Rust change: **rejected** as primary outcome; it saves almost no FFI cost versus this evolution’s target.
- **Monolithic “mega struct” without indices** — **Rejected**; would break material/texture indirection and public mental model; keep index-based materials.
- **Scene graph in Rust for locality** — **Deferred** per [Non-goals](#non-goals); largest API disruption.

### Likely touched areas

- `python/tt3de/render_context_rust.py`, `python/tt3de/textual_standalone.py`
- `src/lib.rs`, buffer `*_py.rs` modules, `src/primitiv_building/mod.rs`, `src/raster/mod.rs`, `src/drawbuffer/` as needed for arena ownership
- Tests under `tests/tt3de/`, `cargo test` / `uv run pytest` per [AGENTS.md](../../AGENTS.md)

## Usability and documentation

- Update **`source/low_level_api.rst`** with a short **“Frame execution model”** subsection: Python owns scene graph sync; Rust owns batched pipeline execution and recommended buffer access patterns.
- **`source/high_level_api.rst`** — Note that `RustRenderContext.render` is the high-level entry; low-level `*_py` functions remain for tooling if exported.
- Migration: if any symbol is deprecated, list replacements in the same doc pass.

## Testability

- **Regression** — Existing raster/material tests and representative demos (`demos/3d/triangle_test.py`, TTSL demos) must produce **pixel-identical or documented-equivalent** output for fixed seeds/camera (where determinism already holds).
- **New** — Unit test (Rust or Python) that asserts **one** `render()` does not require multiple Python-invoked `build_primitives_py` for a normal frame (e.g. mock counter on the binding layer, or internal telemetry flag in test builds only).
- **Resize** — Test `update_wh` after unified path: no stale pointers, drawing dimensions match `Region` in `to_textual_2`.

## Complexity and scope

- **Size: L** — Touches the core render FFI boundary and possibly multiple buffer Py classes.
- **Risk hotspots** — PyO3 borrow rules when merging ownership; parallel material pool lifetime vs arena; `DrawingBufferPy` recreation on resize.
- **Incremental rollback** — Keep the old `*_py` exports behind a **feature flag or compile cfg** only if maintenance cost is low; otherwise land atomically with strong tests. Prefer **single PR** with clear commits over half-migrated ownership.

## A priori performance analysis

### Ranked hypotheses (likely impact for tt3de-scale workloads)

| Rank | Mechanism | Expected effect | When it matters most |
|------|-----------|-------------------|----------------------|
| 1 | **Single native frame orchestration** | Removes several full **Python→Rust→Python** transitions per frame (argument unpack, borrow setup) around the same buffers. | **Low triangle count**, high refresh / Textual redraw — fixed FFI cost rivals raster work. |
| 2 | **Fewer Rust heap objects / allocators** | One (or few) arena regions vs many independent `Vec` backing stores → less **malloc/free churn** on growth, fewer cache misses on **metadata** (struct headers, capacity fields). | Resize, first frames after loading assets, dynamic `add_*` patterns. |
| 3 | **Hot-loop spatial locality** | If geometry + vertex + primitive data for the raster pass land in **fewer cache lines**, inner loops *might* see a measurable win. | Larger vertex/primitive counts within the engine’s “small scene” band; **unproven** until profiled. |

### What the arena alone probably does *not* fix

- **Per-pixel cost** — `drawing_buffer` dimensions × material complexity still dominate once geometry is non-trivial; arena layout does not shrink the number of shaded pixels.
- **Python-side `sync_in_context`** — Today each dirty node can call `rc.transform_buffer.set_node_transform(...)` (`python/tt3de/tt_3dnodes.py` pattern). That remains **many small PyO3 calls** unless a **separate** batching evolution adds “flush transform deltas in one call.” This evolution’s arena is about **Rust storage layout + unified render**; graph traversal cost is largely unchanged unless follow-up work batches sync.
- **Index indirection** — `material_id` → material table → texture table is still **indirect**; the arena packs **storage**, not the logical shader binding model.

### Honest summary

- **Largest predictable win**: fewer FFI boundaries around the render pipeline (**goal 1**), not the arena in isolation.
- **Arena**: meaningful for **engineering invariants** (single Rust mutation context, growth policy, future SIMD-friendly layout) and **probable** small-to-moderate CPU wins on allocation-bound paths; treat **microsecond-level frame gains** as **measurement-dependent**, not guaranteed.
- **Transparent shade pass** — Still **serial** `apply_material` in the baseline pipeline; this evolution does not require parallel transparent shading.

**Validation** — Optional Rust `tracing` spans or debug-only timers around each internal phase; compare frame time distributions on `scripts/screenshot_apps/` workloads before/after. Add a **before/after allocator call counts** (platform-specific) or Rust-only microbench for “N inserts + one frame” if the team wants hard evidence on arena value separate from FFI batching.

## Risks and open questions

- **PyO3 `PyRefMut` ordering** — Unified entry must not create conflicting mutable borrows across nested `PyRefMut` types; may require **interior mutability** (`RwLock`/`Mutex` on arena) or **owned `Arc<Mutex<>>`** patterns—evaluate against tt3de’s “no unnecessary locks in hot loop” standard.
- **Debugger / buffer_views** — Tools that read individual buffers must still see consistent mid-frame state (likely “post-render” only unless snapshot API is defined).
- **Material parallel pool** — `DrawingBufferPy` thread pool and arena layout must stay compatible; document if parallel opaque shading requires pool-on-arena constraints.

## Decision record

*Unfilled — populate when the approach (arena layout vs thin wrappers, exact Py API) is frozen and shipped or closed.*

## References

- [`source/low_level_api.rst`](../../source/low_level_api.rst) — buffer roles and two-pass depth model.
- [`python/tt3de/render_context_rust.py`](../../python/tt3de/render_context_rust.py) — current `render()` sequencing.
- [`src/primitiv_building/mod.rs`](../../src/primitiv_building/mod.rs) — `build_primitives_py` / `apply_material_py` signatures.
