# Evolution: Single-buffer draw path, configurable ASCII blending, and transparency pass qualification

```yaml
id: evol-transparency-depth-layers
status: proposed
created: 2026-05-11
updated: 2026-05-14
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

**Pivot:** Stop treating the terminal rasterizer's multi-layer per-cell stack (`DepthBufferCell` with `L > 1`, K-buffer-style insertion and far-to-near resolve) as the primary transparency strategy. Evolve toward a **single stored fragment per cell** for depth-tested geometry, coupled with a **separate transparency pass** whose compositing is driven by a **configurable ASCII blending system**.

Unlike GPU pixel pipelines, tt3de renders to a terminal cell grid where each cell has three channels (`front_color`, `back_color`, `glyph`). Blending must respect this model. This evolution introduces a **`BlendMode` enum** — designed to grow — starting with `Replace`, `AlphaBlend` (straight alpha, source-over), `Additive`, and ASCII-native modes like `GlyphDither` (coverage via glyph choice) and `HalfBlockComposite` (two-color-per-cell via Unicode half-blocks). Blend mode is configured **per-material** (with per-primitive override), dispatched through a single centralized function, not scattered across material implementations. A **`GlyphPolicy`** (`PreserveExisting` / `ReplaceFromShader`) makes glyph handling explicit during the transparency pass.

This evolution scopes two concrete workstreams:

1. **Draw buffer + fragment resolve redesign** — One depth winner per cell for the relevant pass(es), and a centralized, code-central blending contract with configurable modes from shader `vec4` outputs. Mapping: transparent pass blends **only `front_color`**; `back_color` and `glyph` are set by the opaque pass.
2. **Geometry qualification** — A clear, API-visible way to mark primitives (or materials / draw batches) as belonging to the **opaque pass** vs the **transparency pass**, so the rasterizer can apply the right depth and blend behavior. Mechanism: boolean `transparent` field on `PrimitivReferences`, default `false`.

Ordering artifacts for transparent overlap remain a known limitation unless a separate sort or heavier OIT is added later; this doc does **not** promise order-independent correctness. The blending architecture is, however, designed to be extended when such techniques are added.

## Motivation and context

Today, visibility and partial transparency lean on **`DrawBuffer<L, _>` with `L == 2`** in Python (`DrawingBufferPy`): `set_depth_content` keeps nearest-first layers, overflow fragments drop, and `apply_material_on` resolves **far-to-near** into one `CanvasCell`. Materials toggle subsets of channels (`StaticColor`, `BaseTexture`, etc.). This model is compact for ASCII-scale grids but couples transparency to a **fixed small K-buffer** — there is **zero blending logic** in the engine today; every material implementation unconditionally overwrites `CanvasCell` fields. Transparency is approximated entirely through multi-layer stacking and far-to-near overwrite order.

Moving to a **single-buffer per pass** model clarifies semantics: two separate `DrawBuffer<1, f32>` instances (one opaque, one transparent) replace the shared `DrawBuffer<2, f32>`. The opaque pass stores **at most one depth-winning fragment per cell** (nearest-wins, depth write on). The transparency pass stores qualified geometry with depth test on but depth write off, then composes results onto the opaque canvas using a **configurable per-material `BlendMode`** dispatched through a single centralized function. This decouples transparency from the K-buffer size and makes the compositing contract explicit, testable, and extensible for ASCII-specific techniques.

## Goals

- **Single-layer draw storage (per pass):** Redesign the draw buffer path into **two separate `DrawBuffer<1, f32>` instances** — one for the opaque pass (depth test + write, nearest-wins), one for the transparency pass (depth test on, depth write off, composited onto opaque results). The generic `L` parameter in `DepthBufferCell<A, L>` stays at `1` for both.
- **Configurable ASCII blending:** Introduce a **`BlendMode` enum** stored **per-material** (with per-primitive override) dispatched through a single centralized Rust function. Initial modes include `Replace` (current behavior), `AlphaBlend` (straight alpha, source-over), `Additive`, and ASCII-native modes: `GlyphDither` (coverage via glyph choice), `HalfBlockComposite` (two colors per cell via Unicode half-blocks). Designed to grow — new modes are a single enum variant + match arm + tests.
- **Explicit GlyphPolicy:** The transparency pass carries an explicit **`GlyphPolicy`** (`PreserveExisting` / `ReplaceFromShader`) so glyph handling during compositing is not ambiguous. Default: `PreserveExisting` — the opaque pass owns the glyph; transparent fragments only affect `front_color`.
- **Transparency pass qualification:** Introduce a **boolean `transparent` field on `PrimitivReferences`** (default `false`), threaded from Python scene setup through primitive building into rasterization, enabling the rasterizer to filter primitives per pass.
- **Documentation:** Update canonical docs (`source/low_level_api.rst` and cross-links) so the model is **discoverable** and contrasts clearly with the old multi-layer resolve where needed.

## Non-goals (initial slice)

- Full **order-independent transparency** (A-buffer, depth peeling, weighted blended OIT, etc.) as a default requirement.
- **Increasing `L`** globally as the main fix for transparency (the old "more K-buffer layers" direction is deprecated relative to this evolution).
- Perfect transparency for **intersecting** transparent triangles without an explicit sort or heavier technique (may remain documented limitation).
- **Per-material blend factor customizability** beyond the `BlendMode` enum (e.g., arbitrary source/destination factor pairs, premultiplied alpha toggle). The initial slice ships a curated set of modes; adding factors is future work.
- **Comprehensive coverage of all ASCII art blending techniques** — the `BlendMode` system is a **foundation** for growth, not a complete catalog. New modes can be added as the engine's artistic use cases evolve.

## User-visible functionality

- **Breaking / behavior change potential:** Default rendering may change where scenes depended on **two-layer stacking** or overflow-drop semantics. A **`legacy_layers=True`** parameter on `DrawingBufferPy` (default `True` with `DeprecationWarning`) preserves the old `L=2` path during migration. Migration notes for the transition belong in the implementation PR and docs.
- **After implementation:** Authors can **tag** geometry or materials for opaque vs transparent passes (boolean `transparent` on primitives, default `false`). Materials declare their **`BlendMode`** (initial set: `Replace`, `AlphaBlend`, `Additive`, `GlyphDither`, `HalfBlockComposite`). Transparency compositing follows the configured blend mode via a centralized dispatch, and the **`GlyphPolicy`** (`PreserveExisting` / `ReplaceFromShader`) controls whether transparent fragments can modify the cell glyph.

## Technical approach

### 1. Draw buffer and fragment resolve — two-buffer architecture

- **Buffer layout:** Two separate `DrawBuffer<1, f32>` instances replace the current shared `DrawBuffer<2, f32>`. The opaque buffer stores one depth-winning fragment per cell (nearest-wins via `set_depth_content` with `L=1`, which degenerates correctly: the single layer either replaces or drops on depth comparison). The transparent buffer also uses `L=1` but with depth test on / depth write off — fragments test against the opaque buffer's resolved depth but do not modify it.

- **Opaque pass:** Standard depth test + nearest-wins per cell. Fragment shader output (`vec4`) writes into the resolved cell state — by convention, the first `vec4` maps to `front_color`, the second `vec4` maps to `back_color` (though blending does not apply here), and the `i32` maps to `glyph`. No blending occurs; the opaque winner fully owns the cell's three channels.

- **Transparency pass:** Second rasterization pass over **qualified** (transparent-tagged) geometry. Each fragment:
  1. Passes the depth test (compares against opaque buffer's resolved depth) — occluded fragments are culled.
  2. Does **not** update the depth buffer (depth write off).
  3. Is composited onto the existing cell via a centralized **`BlendMode` dispatch** function, applied to `front_color` only. `back_color` and `glyph` are left unchanged from the opaque pass (subject to `GlyphPolicy` — see below).

- **Blend function location:** A single free function (or small module `blend.rs` under `drawbuffer/`) that takes `(dst: &Color, src: &Vec4, mode: &BlendMode) -> Color`. This function is the **only** place blend math lives — materials do not implement blending themselves. Tests assert representative alpha values and overwrite-vs-accumulate cases here.

- **CanvasCell mapping for transparency pass:** Only `front_color` is blended. The transparent fragment's shader output `(vec4 front, vec4 back, i32 glyph)` — only the first `vec4` is used. `back_color` and `glyph` carry over from the opaque pass. If the `GlyphPolicy` is `ReplaceFromShader`, the glyph is replaced; default is `PreserveExisting`.

### 2. Fragment shader / material output contract

- **Alpha convention:** **Straight alpha, source-over** for the `AlphaBlend` mode: `result = src * src.a + dst * (1 - src.a)`. This is the default blend equation and is documented as the project convention. Premultiplied alpha is not supported in the initial slice.

- **`BlendMode` enum** (stored per-material):
  ```rust
  enum BlendMode {
      Replace,            // src overwrites dst entirely (no blending, current behavior)
      AlphaBlend,         // Straight alpha source-over: src * src.a + dst * (1 - src.a)
      Additive,           // dst + src (clamped to [0,1] per channel)
      GlyphDither,        // Coverage approximated via glyph character selection
      HalfBlockComposite, // Two colors per cell resolved via Unicode half-block glyph
  }
  ```
  Designed for extension — adding a mode is one new variant + one match arm in the dispatch function + tests.

- **`GlyphPolicy`** (carried alongside the blend config):
  ```rust
  enum GlyphPolicy {
      PreserveExisting,   // Transparent pass does not modify glyph (default)
      ReplaceFromShader,  // Shader's glyph output replaces the cell glyph
  }
  ```

- **Per-material storage:** Material implementations (`StaticColor`, `ShaderPy`, `BaseTexture`, etc.) grow a `blend_mode: BlendMode` field and a `glyph_policy: GlyphPolicy` field. The primitive buffer can override these per-instance if needed, with precedence: primitive-level override > material default.

### 3. Geometry qualification for transparency pass

- **Storage:** A boolean `transparent: bool` field on `PrimitivReferences` (shared by all `PrimitiveElements` variants). Default `false`. No enum — binary opaque/transparent is sufficient for the initial slice; expanding to a multi-pass system is future work.

- **Rasterizer integration:** `raster_all` gains a `pass_filter: Option<PassTag>` parameter:
  ```rust
  enum PassTag { Opaque, Transparent }

  fn raster_all<const DEPTHCOUNT: usize>(
      primitivbuffer: &PrimitiveBuffer,
      vertexbuffer: &VertexBuffer<Vec4>,
      drawing_buffer: &mut DrawBuffer<DEPTHCOUNT, f32>,
      pass_filter: Option<PassTag>,  // None = all primitives, Some = filtered
  )
  ```
  The rendering pipeline calls `raster_all` twice per frame: once with `Opaque` (into the opaque buffer), once with `Transparent` (into the transparent buffer, which then composites onto the same canvas).

- **Python surface:** `TT3DPolygon`, `TT3DNode`, and related scene objects expose a `transparent: bool` property (default `False`). This is threaded through `build_primitives` into `PrimitivReferences`. Materials expose a `blend_mode` property and `glyph_policy` property. Example:
  ```python
  poly = TT3DPolygon(vertex_list=..., triangles=..., material_id=5)
  poly.transparent = True
  # Or per-material:
  material.blend_mode = "alpha_blend"
  material.glyph_policy = "preserve_existing"
  ```

### 4. Ordering

- The transparent pass composites fragments in **raster iteration order** (the order primitives appear in the primitive buffer). For correct transparency with overlapping transparent geometry, a **back-to-front sort** by depth key is required.
- **If sort ships in this milestone:** The sort key is **centroid Z** in NDC space, computed during primitive building or before the transparent raster pass. Transparent primitives are sorted back-to-front before the transparent `raster_all` call. This adds complexity **M** — requires a sort pass and interaction with buffer clears.
- **If sort is deferred:** The transparent pass composites in arbitrary (raster) order. Overlapping transparent fragments produce ordering-dependent results, documented as a known limitation.
- **Decision:** This must be settled before implementation — see Decision record.

### Alternatives considered

- **Retain K-buffer as primary:** Rejected as the target architecture for this evolution (may remain internally for a `legacy_layers` compatibility mode unless fully removed).
- **Infer transparency pass from alpha threshold only:** Rejected as sole mechanism — explicit qualification is required for stable pipeline control and API clarity.
- **Single shared `DrawBuffer<2, f32>` with per-layer pass targeting:** Rejected in favor of two separate `DrawBuffer<1, f32>` instances. Shared buffer risks accidental cross-pass fragment mixing and makes depth write semantics harder to enforce correctly per pass.
- **Per-draw-batch qualification:** Rejected for the initial slice. Per-primitive qualification is simpler, more flexible, and requires no structural changes to the render loop organization.

## Usability and documentation

- One canonical section in **`source/low_level_api.rst`** describing: two-buffer architecture (opaque + transparent), **`BlendMode`** enum and its semantics, **`GlyphPolicy`**, per-material blend configuration, depth semantics per pass, and the alpha convention (straight, source-over).
- README or **`source/high_level_api.rst`** short pointer to that section ("rendering model" + "blending").
- **Migration note** in the docs showing before/after for a common case: two overlapping semi-transparent triangles that previously worked via K-buffer stacking, now requiring `transparent=True` and accepting ordering limitations.
- Demos using transparency should mention **pass tagging**, **blend mode**, and **sort limitations** in comments where relevant.

## Testability

### Blend math (unit tests — Rust)

A centralized dispatch function `blend(dst: &Color, src: &Vec4, mode: &BlendMode) -> Color` is tested against this matrix:

| # | dst (front) | src (front vec4) | mode | Expected front | Rationale |
|---|---|---|---|---|---|
| 1 | (1,0,0,1) | (0,1,0,1) | Replace | (0,1,0,1) | Full opaque replace |
| 2 | (1,0,0,1) | (0,1,0,0.5) | AlphaBlend | (0.5,0.5,0,1) | Straight alpha: src*0.5 + dst*0.5 |
| 3 | (1,1,1,1) | (0,0,0,0) | AlphaBlend | (1,1,1,1) | Alpha 0 = no change |
| 4 | (0,0,0,1) | (1,0,0,1) | Additive | (1,0,0,1) | Full add |
| 5 | (0.5,0,0,1) | (0,0,1,1) | Additive | (0.5,0,1,1) | Clamped add |
| 6 | (1,1,1,1) | (2, -1, 0.5, 2) | AlphaBlend | (1,0,0.5,1) | Channel clamp to [0,1] |

### Glyph / front / back interaction (unit tests — Rust)

| # | Before cell (front, back, glyph) | Fragment (front vec4, back vec4, glyph i32) | GlyphPolicy | Expected cell (front, back, glyph) | Rationale |
|---|---|---|---|---|---|
| 1 | (0,0,1,1), (0,0,0,1), 219 | (1,0,0,0.5), (0,0,1,0.5), 0 | PreserveExisting | (0.5,0,0.5,1), (0,0,1,1), 219 | Transparent overlay doesn't erase glyph |
| 2 | (0,0,1,1), (-,-), 32 | (1,0,0,1), (-,-), 65 | ReplaceFromShader | (1,0,0,1), (-,-), 65 | Opaque foreground on trans pass replaces glyph |
| 3 | (0,0,1,1), (0.5,0,0,1), 219 | (1,0,0,0.5), (-,-), 219 | PreserveExisting | (0.5,0,0.5,1), (0.5,0,0,1), 219 | Back color unchanged by trans pass |

### Performance benchmarks

- **Method:** `cargo bench` or pytest-benchmark on an 80×24 grid with mixed opaque/transparent content
- **Baseline:** Current `DrawBuffer<2>` with single `raster_all + apply_material_on`
- **Proposed:** Two-buffer approach with opaque + transparent raster passes
- **Acceptable threshold:** < 20% regression on mixed opaque/transparent scenes
- **Worst-case test:** All primitives tagged transparent (double pass, no depth write)

### Regression detection

- **Git archeology:** Before the change, identify all demos and tests with overlapping semi-transparent content by searching `material_id` assignments, alpha values < 1 in material setup, and shader returns with alpha < 1.
- **Reference snapshots:** Run key demos before the change, capture `to_textual_2()` output. After the change, diff against references.
- **Known-risk patterns:** StaticColor with alpha < 255 on back_color, overlapping triangles with same shader outputting alpha < 1, glyph-0 overlays used as transparent cover.

### BlendMode dispatch tests

Each mode gets at minimum: one happy path (known inputs → known output), one edge case (clamping, zero alpha, full alpha).

## Complexity and scope

### File change inventory (~18 files)

| Category | Files | Tag |
|---|---|---|
| **Buffer architecture** | `src/drawbuffer/drawbuffer.rs` | MODIFY — add `blend.rs` submodule, two-buffer pipeline, BlendMode dispatch |
| **Buffer architecture** | `src/drawbuffer/mod.rs` | MODIFY — DrawingBufferPy L=2→1, `legacy_layers` compat, blend config exposure |
| **Buffer architecture** | `src/drawbuffer/blend.rs` | NEW — BlendMode enum, GlyphPolicy, blend dispatch function |
| **Rasterization** | `src/raster/mod.rs` | MODIFY — `raster_all` gets pass filter parameter |
| **Rasterization** | `src/raster/raster_triangle_tomato.rs` | MODIFY — `set_depth_content` usage per pass (depth write on/off) |
| **Primitive system** | `src/primitivbuffer/mod.rs` | MODIFY — `transparent: bool` on PrimitivReferences |
| **Primitive system** | `src/primitiv_building/mod.rs` | MODIFY — thread `transparent` through build pipeline |
| **Materials** | `src/material/mod.rs` | MODIFY — RenderMaterial trait gets blend_mode/glyph_policy |
| **Materials** | `src/material/static_color.rs` | MODIFY — add blend_mode, glyph_policy fields |
| **Materials** | `src/material/shader_material.rs` | MODIFY — add blend_mode, glyph_policy fields, route through blend dispatch |
| **Materials** | `src/material/textured.rs` | MODIFY — add blend_mode, glyph_policy fields |
| **Bindings** | `src/lib.rs` | MODIFY — register new types, submodules if any |
| **Python wrappers** | `python/tt3de/*.py` | MODIFY — TT3DPolygon.transparent, material.blend_mode, etc. |
| **Python pipeline** | `python/tt3de/render_context_rust.py` | MODIFY — two-pass rendering loop |
| **Tests (Rust)** | `src/drawbuffer/blend.rs` (tests) | NEW — blend math and glyph interaction tests |
| **Tests (Python)** | `tests/tt3de/test_r_draw_buffer.py` | MODIFY — adapt for single-buffer, add blend tests |
| **Tests (bench)** | `tests/benchs/` or `benches/` | MODIFY — add two-pass benchmark |
| **Docs** | `source/low_level_api.rst` | MODIFY — new rendering model section |
| **Deprecated** | `src/drawbuffer/legacy_layers.rs` (or inline) | NEW — hold old L=2 path for compat, to be removed |

### Complexity per workstream

- **Draw buffer + blend architecture:** **L** — touches buffer allocation, raster pass structure, centralized blend function, per-material config fields on every material variant. The most invasive workstream.
- **Qualification API:** **M** — boolean on PrimitivReferences, Python property on TT3DPolygon etc., pass filter parameter on `raster_all`.
- **Backwards compatibility layer:** **M** — `legacy_layers=True` mode, deprecation warnings, dual-test-path maintenance until removal.
- **Optional transparent sort (same milestone):** **M** — centroid Z computation, sort pass, interaction with buffer clears.

Incremental shipping is possible: introduce qualification + transparent pass first behind `legacy_layers=False` opt-in, validate with test matrix and benchmarks, then remove multi-layer paths once old L=2 behavior is confirmed no longer needed — see Decision record for sequencing.

## Risks and open questions

- **Breaking visuals** for content depending on two-layer stacking or overflow drops. Mitigation: `legacy_layers=True` default with deprecation warning, migration guide with before/after examples.
- **Glyph/front/back mapping resolution** (chosen: transparent pass blends only front_color, preserves back_color and glyph). Risk: this mapping may not suit all use cases (e.g., decals that should also affect back_color). Mitigation: document as v1 contract; future BlendMode variants can target back_color independently.
- **BlendMode enum design** — too many initial modes could over-commit to unproven techniques (GlyphDither, HalfBlockComposite). Risk: some modes may prove impractical and need deprecation. Mitigation: implement the dispatch framework with Replace + AlphaBlend + Additive as "always-stable" core; mark ASCII-specific modes as "experimental" until validated with real demos.
- **Per-material config bloat** — every material variant grows blend_mode and glyph_policy fields. Risk: constructor ergonomics degrade. Mitigation: provide sensible defaults (Replace, PreserveExisting) so only transparency-specific materials need explicit config.
- **Change surface area** — ~18 files touched, const generic `<2>` threaded through raster/material/test code. Risk: subtle type-level breakage. Mitigation: `cargo check --all-targets` after every change block.
- **Performance** — second raster pass could double rasterization time. Mitigation: benchmark before merge; if >20% regression on mixed scenes, consider merging opaque+transparent into a single raster pass that dispatches per-primitive (trades code complexity for runtime cost).
- **Sort key** for transparent primitives if sort ships with this evolution — centroid Z vs min depth vs z-buffer value. Risk: wrong sort key produces visible artifacts that look like bugs. Mitigation: centroid Z with deterministic tiebreaking (primitive ID); document that intersecting transparent triangles are not handled correctly (non-goal).

## Decision record

- **Status:** proposed
- **Resolution:** Adopt the following architecture for implementation:
  1. **Two separate `DrawBuffer<1, f32>` instances** (opaque + transparent), not a shared buffer.
  2. **`BlendMode` enum** per-material with centralized dispatch. Initial modes: `Replace`, `AlphaBlend` (straight alpha, source-over), `Additive`, `GlyphDither` (experimental), `HalfBlockComposite` (experimental).
  3. **`GlyphPolicy`** (`PreserveExisting` / `ReplaceFromShader`) — default `PreserveExisting`.
  4. **Transparency pass blends only `front_color`** — `back_color` and `glyph` from opaque pass.
  5. **Per-primitive `transparent: bool`** on `PrimitivReferences` (default `false`) for geometry qualification.
  6. **`legacy_layers=True`** on `DrawingBufferPy` (default `True` with `DeprecationWarning`) for backwards compatibility.
  7. **Sort:** Deferred to follow-up milestone. The transparent pass composites in raster iteration order; overlapping transparent artifacts are a documented limitation.
  8. **Sequencing:** (a) BlendMode enum + blend dispatch + tests → (b) per-material config on existing materials → (c) transparent flag + pass filter → (d) two-pass rendering pipeline → (e) legacy compat layer → (f) benchmarks + regression audit → (g) remove dead L=2 paths in a subsequent chore PR.

## References

- `source/low_level_api.rst` — Drawing Buffer, depth resolve (to be revised)
- `src/drawbuffer/drawbuffer.rs` — `DrawBuffer`, `DepthBufferCell`, `CanvasCell`
- `src/drawbuffer/mod.rs` — `DrawingBufferPy`, `layer_count`
- `src/drawbuffer/blend.rs` — `BlendMode`, `GlyphPolicy`, blend dispatch (new)
- `src/material/shader_material.rs` — vec4 → cell mapping
- `src/raster/mod.rs` — `raster_all` primitive iteration order
