# Evolution: Single-buffer draw path, vec4 blending, and transparency pass qualification

```yaml
id: evol-transparency-depth-layers
status: proposed
created: 2026-05-11
updated: 2026-05-11
authors: []
supersedes: []
superseded-by: ""
related:
  - source/low_level_api.rst       # Drawing Buffer + depth resolve (update after implementation)
  - src/drawbuffer/drawbuffer.rs    # DrawBuffer, DepthBufferCell<L>, CanvasCell
  - src/drawbuffer/mod.rs           # DrawingBufferPy (currently L = 2)
  - src/material/shader_material.rs # Fragment-style shading, vec4 registers → CanvasCell
  - src/raster/mod.rs               # raster_all: primitive iteration order
```

## Summary

**Pivot:** Stop treating the terminal rasterizer’s multi-layer per-cell stack (`DepthBufferCell` with `L > 1`, K-buffer-style insertion and far-to-near resolve) as the primary transparency strategy. Evolve toward a **single stored fragment per cell** for depth-tested geometry, coupled with a **separate transparency pass** whose compositing is driven by **explicit color blending rules** applied when resolving **fragment shader output as `vec4`** (RGBA).

This evolution scopes two concrete workstreams:

1. **Draw buffer + fragment resolve redesign** — One depth winner per cell for the relevant pass(es), and a documented, code-central blending contract from shader `vec4` outputs ( Straight vs premultiplied alpha, destination conventions, and interaction with `CanvasCell` front/back/glyph channels should be pinned down in implementation and docs.)
2. **Geometry qualification** — A clear, API-visible way to mark primitives (or materials / draw batches) as belonging to the **opaque pass** vs the **transparency pass**, so the rasterizer can apply the right depth and blend behavior without relying on implicit multi-layer stacking.

Ordering artifacts for transparent overlap remain a known limitation unless a separate sort or heavier OIT is added later; this doc does **not** promise order-independent correctness.

## Motivation and context

Today, visibility and partial transparency lean on **`DrawBuffer<L, _>` with `L == 2`** in Python (`DrawingBufferPy`): `set_depth_content` keeps nearest-first layers, overflow fragments drop, and `apply_material_on` resolves **far-to-near** into one `CanvasCell`. Materials toggle subsets of channels (`StaticColor`, `BaseTexture`, etc.). That is compact for ASCII-scale grids but couples transparency to a **fixed small K-buffer** and makes it harder to align mental models with “one depth sample + blend stage” pipelines.

Moving to a **single-buffer** model per pass clarifies semantics: each cell holds **at most one depth-associated fragment** for opaque geometry; transparent geometry is composed in a **second pass** with **explicit blend equations** fed by **shader `vec4` color output**, reducing reliance on multi-layer insertion policy for everyday transparency.

## Goals

- **Single-layer draw storage (per pass):** Redesign the draw buffer path so the primary opaque resolve uses **one depth slot per cell** (conceptually `L == 1` for that pass, or equivalent semantics without multi-layer competition).
- **Explicit blending:** Define and implement **deterministic blending rules** when applying fragment results to the canvas (including alpha), with fragment shaders contributing **`vec4`** colors whose interpretation (e.g. straight RGBA) is documented and tested.
- **Transparency pass qualification:** Introduce a stable mechanism (primitive flag, material metadata, or batch/scene flag — TBD in design) so geometry is explicitly **opaque-pass** vs **transparency-pass**, enabling correct depth/blend stage selection without inferring from ad hoc material behavior alone.
- **Documentation:** Update canonical docs (`source/low_level_api.rst` and cross-links) so the model is **discoverable** and contrasts clearly with the old multi-layer resolve where needed.

## Non-goals (initial slice)

- Full **order-independent transparency** (A-buffer, depth peeling, weighted blended OIT, etc.) as a default requirement.
- **Increasing `L`** globally as the main fix for transparency (the old “more K-buffer layers” direction is deprecated relative to this evolution).
- Perfect transparency for **intersecting** transparent triangles without an explicit sort or heavier technique (may remain documented limitation).

## User-visible functionality

- **Breaking / behavior change potential:** Default rendering may change where scenes depended on **two-layer stacking** or overflow-drop semantics; migration notes and optional compatibility shims (if any) belong in the implementation PR and docs.
- **After implementation:** Authors can **tag** geometry or materials for opaque vs transparent passes; transparency compositing follows **documented vec4 blending** rather than implicit multi-layer material ordering alone.

## Technical approach

### 1. Draw buffer and fragment resolve (single-buffer style)

- **Opaque pass:** Standard **depth test + single winner per cell**; fragment output **`vec4`** writes into the resolved cell state under fixed rules (replacing or initializing canvas channels as specified).
- **Transparency pass:** Second rasterization pass over **qualified** geometry with **depth test appropriate to transparency** (typically test-on, write-off vs opaque — exact mirror of chosen semantics must be documented), composing **`vec4`** results onto the existing canvas using the **explicit blend functions** (source/destination factors and order fixed in code + docs).
- **Canvas mapping:** Preserve or intentionally evolve how **`vec4`** maps to `CanvasCell` (front/back/glyph). Any reduction from two physical depth layers may simplify far-to-near iteration in `apply_material_on`-style paths; implementation should **centralize** blend + channel writes so materials do not each reimplement alpha policy ad hoc.

### 2. Fragment shader / material output contract

- Treat the relevant fragment stage output as **`vec4` RGBA** (already present in register paths in places like `shader_material.rs`); lock **alpha convention** (straight vs premultiplied) project-wide for this pipeline.
- **Explicit blending rules** live next to resolve code (Rust), not only in prose, so tests can assert behavior for representative alpha values and overwrite vs accumulate cases.

### 3. Geometry qualification for transparency pass

- **Minimum viable:** A per-primitive or per-draw **boolean or enum** (`Opaque` / `Transparent`) carried from Python/Rust scene setup through primitive building into rasterization, filtering which pass runs which primitives.
- **Alternative / additive:** Material-level defaults with per-instance override; document precedence (e.g. primitive wins over material default).

### 4. Ordering

- Transparent pass may still require **back-to-front sort** by depth key for plausible results when multiple transparent fragments compete for the same cell; that can be a **follow-on** or a tightly scoped part of this evolution if included in the same milestone—call out in decision record.

### Alternatives considered

- **Retain K-buffer as primary:** Rejected as the **target architecture** for this evolution (may remain internally for specialized modes unless fully removed).
- **Infer transparency pass from alpha threshold only:** Rejected as sole mechanism — explicit qualification is required for stable pipeline control and API clarity.

## Usability and documentation

- One canonical section in **`source/low_level_api.rst`** describing: single-buffer opaque resolve, transparency pass, **`vec4`** alpha convention, and blend equations.
- README or **`source/high_level_api.rst`** short pointer to that section (“rendering model”).
- Demos using transparency should mention **pass tagging** and **sort limitations** in comments where relevant.

## Testability

- **Unit / Rust tests:** Depth winner replacement vs transparent overlay; blend math edge cases (alpha 0/1, saturation).
- **Python tests:** Mirror patterns in `tests/tt3de/test_r_draw_buffer.py` (and related) for regressions on canvas output when qualifying geometry.
- **Contrast tests:** Scenes that previously relied on **two-layer** behavior get explicit expectations updated or marked deprecated.

## Complexity and scope

- **Draw buffer + resolve + blending:** **L** — touches `drawbuffer`, raster insertion, material/shader resolve, possibly TTSL docs if register semantics are user-visible.
- **Qualification API:** **M** — primitive buffer, bindings, materials, demos.
- **Optional transparent sort in same milestone:** **M** — additional sort pass and interaction with buffer clears.

Incremental shipping is possible: introduce qualification + dual-pass framing first behind clear defaults, then remove or dead-code multi-layer paths once behavior is validated — exact sequencing is an implementation choice captured in the decision record.

## Risks and open questions

- **Breaking visuals** for content depending on two-layer stacking or overflow drops.
- **Alpha convention** inconsistency between materials unless centralized.
- **Glyph / dual-channel (`front_color` / `back_color`)** interaction with single **`vec4`** blend — may need a small set of approved material modes rather than arbitrary per-material blend factors at first.
- **Sort key** for transparent primitives if sort ships with this evolution (centroid vs min depth, etc.).
- **Performance:** Second pass over transparent subset vs previous fixed `L=2` cost — profile on representative demos.

## Decision record

- **Status:** proposed  
- **Resolution (directional):** Adopt **single-buffer-per-pass** semantics with **explicit `vec4`-driven blending** and **explicit geometry qualification** for the transparency pass as the targeted evolution; deprecate reliance on multi-layer K-buffer behavior as the primary transparency mechanism. Final milestone boundaries (sort included or not, compatibility shims) to be set when implementation is scheduled.

## References

- `source/low_level_api.rst` — Drawing Buffer, depth resolve (to be revised)
- `src/drawbuffer/drawbuffer.rs` — `DrawBuffer`, `DepthBufferCell`, `CanvasCell`
- `src/drawbuffer/mod.rs` — `DrawingBufferPy`, `layer_count`
- `src/material/shader_material.rs` — vec4 → cell mapping
- `src/raster/mod.rs` — `raster_all` primitive iteration order
