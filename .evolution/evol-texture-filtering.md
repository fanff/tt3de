# Evolution: Per-Texture Filter Mode (Nearest / Bilinear)

```yaml
id: evol-texture-filtering
status: in-progress
created: 2026-05-14
authors: []
supersedes: []
superseded-by: ""
related:
  - demos/3d/dust.py                   # Motivation: rough underscale textures
  - source/low_level_api.rst           # Texture buffer and material pipeline
  - source/ttsl.md                     # tt_texture builtin
```

## Summary

Add a per-texture **filter mode** — `Nearest` (point sampling) or `Bilinear` (4-texel linear interpolation) — stored on each texture and respected by all sampling paths: the `Textured`/`BaseTexture` material renderer and the TTSL `tt_texture` builtin. The filter mode is a **texture property**, set at creation time, not a per-sample shader parameter. The default is `Bilinear`, fixing aliasing from nearest-neighbor undersampling (the "pointy/sharp" look when large textures render small). Implementation is **partially started** in `src/texturebuffer/` — the `FilterMode` enum, storage fields, `uv_map_inline` branching, texture-buffer plumbing, and Python binding parameter all exist but the code is in an inconsistent state (duplicate code blocks, missing `cargo check --all-targets` verification). No TTSL builtin changes are needed.

## Motivation and context

- **Current behavior**: The `Texture::uv_map_inline` and `TextureCustom::uv_map_inline` methods sample a single nearest texel by truncating UV coordinates to integer pixel indices. This produces the "pixelated/pointy" look observed in the Dust 3D demo (`demos/3d/dust.py`) when large textures are displayed at small screen sizes.
- **Problem**: Textures render with extreme aliasing under minification. No filtering exists.
- **Reference**: Standard rasterizers use bilinear filtering as the baseline (GPU `GL_LINEAR`, `D3D11_FILTER_MIN_MAG_MIP_LINEAR`). tt3de's CPU-only rasterizer can afford the extra texel reads since the material pass is post-rasterization, not in the inner triangle loop.
- **Scope fit**: CPU rasterization at Textual terminal resolutions (~80–120 cols) means textures are often minified. Bilinear filtering is the right default for tt3de's small-scene, demo-oriented use case.

## Goals

- **Per-texture filter mode** stored as `FilterMode::Nearest` / `FilterMode::Bilinear` on `Texture<SIZE>` and `TextureCustom<SIZE>`.
- **All sampling paths respect filter mode**: `Textured` material, `BaseTexture` material, TTSL `tt_texture` builtin, and atlas textures (delegated automatically).
- **Python API**: `TextureBufferPy.add_texture(..., filter_mode="bilinear")` with `"bilinear"` default. `add_atlas_texture_from_iter` gets the same parameter.
- **Default is bilinear**: matches current bilinear-on branch behavior; no silent visual regression for existing demos.
- **Implementation completed and compiling** (`cargo check --all-targets` clean, `cargo test` passing, `uv run maturin develop` succeeding).

## Non-goals

- **No new TTSL builtin** for runtime filter switching. Filter mode is a texture property, not a per-sample shader parameter. A TTSL builtin (e.g., `tt_setTextureFilter`) can be added later if a concrete use case emerges.
- **No mipmapping**. Bilinear alone doesn't solve extreme minification aliasing (moire). Mip chains are a separate, larger evolution.
- **No anisotropic filtering**. Overkill for tt3de's scale.
- **No texture-atlas filter-mode propagation changes**. Atlas textures delegate to their inner texture's `uv_map`, inheriting filter mode automatically — zero code changes needed.

## User-visible functionality

- Python users can create nearest-neighbor textures:
  ```python
  texture_buffer.add_texture(w, h, pixels, filter_mode="nearest")
  ```
- Default behavior is bilinear — all existing demos and OBJ loaders get bilinear automatically.
- No breaking changes. The `add_texture` signature is extended with a new keyword argument.
- `obj_loader.py` and `asset_fastloader.py` require no changes (they get the bilinear default).
- The Dust 3D demo (`demos/3d/dust.py`) benefits immediately with zero code changes.

## Technical approach

### Baseline (pre-evolution)

- `Texture::uv_map_inline` and `TextureCustom::uv_map_inline` use nearest-neighbor: cast UV to integer texel index, return single texel.
- No filter concept exists. No mipmaps. No sampling control.

### Proposed change

1. **`FilterMode` enum** in `src/texturebuffer/mod.rs`:
   ```rust
   #[derive(Clone, Copy, PartialEq, Debug)]
   pub enum FilterMode { Nearest, Bilinear }
   ```

2. **`filter_mode: FilterMode` field** added to `Texture<SIZE>` and `TextureCustom<SIZE>`.

3. **`uv_map_inline` branching**: In both `Texture` and `TextureCustom`, an early-return path for `FilterMode::Nearest` skips the 4-texel fetch and `lerp_rgba` blend. `Bilinear` follows the full interpolation path.

4. **`lerp_rgba` helper**: `#[inline(always)] fn lerp_rgba(a: RGBA, b: RGBA, t: f32) -> RGBA` (already written, in `mod.rs`).

5. **Texture buffer plumbing**: `make_texture`, `add_texture_from_iter`, `add_atlas_texture_from_iter` in `texture_buffer.rs` accept `filter_mode: FilterMode` and forward it to constructors. `TextureBuffer::new` creates init textures with `FilterMode::Bilinear`.

6. **Python binding**: `TextureBufferPy.add_texture` accepts `filter_mode: &str = "bilinear"` parsed by `parse_filter_mode()`. `add_atlas_texture_from_iter` gets the same parameter.

### Affected subsystems

| Subsystem | Files | Change |
|-----------|-------|--------|
| Rust core | `src/texturebuffer/mod.rs` | `FilterMode` enum, `lerp_rgba`, modified `uv_map_inline`, modified structs, `parse_filter_mode`, updated `TextureBufferPy` methods |
| Rust core | `src/texturebuffer/texture_buffer.rs` | Updated `make_texture`, `add_texture_from_iter`, `add_atlas_texture_from_iter` |
| Rust test | `src/material/textured.rs` | Updated `test_render_mat` (needs `FilterMode` import and parameter) |
| Rust (auto) | `src/texturebuffer/atlas_texture.rs` | Zero changes — delegates to inner `uv_map` |
| Python | `python/tt3de/obj_loader.py` | Zero changes — gets bilinear default |
| Python | `python/tt3de/asset_fastloader.py` | Zero changes — gets bilinear default |
| Demo | `demos/3d/dust.py` | Zero changes — gets bilinear default |

### Current implementation state (in-progress)

The following has been written but is in an **inconsistent, non-compiling state**:

- `FilterMode` enum: **added** (`mod.rs`)
- `filter_mode` field on `Texture` and `TextureCustom`: **added**
- `uv_map_inline` branching (nearest / bilinear): **written** for both structs
- `lerp_rgba`: **written**
- `make_texture`, `add_texture_from_iter`, `add_atlas_texture_from_iter` plumbing: **updated** (`texture_buffer.rs`)
- `parse_filter_mode`: **written** (duplicate copies exist)
- `TextureBufferPy.add_texture` `filter_mode` param: **added**
- `TextureBufferPy.add_atlas_texture_from_iter` `filter_mode` param: **added**
- **Remaining issues**:
  - Duplicate `impl` blocks and duplicate `parse_filter_mode` functions in `mod.rs`
  - `FilterMode` import needed in `src/material/textured.rs` tests
  - Test call sites need `FilterMode::Bilinear` parameter added
  - `add_atlas_texture_from_iter` missing `#[pyo3(signature)]` for `filter_mode` default
  - `parse_filter_mode` placed outside the `#[pymethods] impl` block
  - Has not passed `cargo check --all-targets`

### Future / optional phases

- **Nearest-neighbor tests**: Unit tests verifying exact texel return without interpolation for `FilterMode::Nearest`.
- **TTSL `tt_setTextureFilter` builtin**: If runtime filter switching is needed, add a new opcode and `set_filter` method on `TtslTextureEnv`. Deferred until a concrete use case emerges.

### Alternatives considered

- **Always-on bilinear (no enum)**: Rejected — pixel-art workflows need nearest-neighbor. Keeping an enum is cheap.
- **Per-sample filter parameter on `tt_texture`**: Rejected — violates GPU convention (filter is a texture property) and adds per-sample branching in the VM hot path.
- **Mipmapping as part of this evolution**: Rejected — significantly larger scope (mip chain generation, LOD computation in raster, trilinear sampling). Separate evolution.

## Usability and documentation

- **Python API**: Single new keyword argument `filter_mode="bilinear"` on `add_texture`. Accepted values: `"nearest"`, `"bilinear"`. `ValueError` on unrecognized input.
- **Docs to update**: `source/low_level_api.rst` (texture buffer section — document `filter_mode` parameter). No TTSL doc changes needed.
- **Demos**: Dust demo (`demos/3d/dust.py`) already demonstrates bilinear improvement with zero changes.

## Testability

- **Rust unit tests** (`src/texturebuffer/mod.rs`): `test_texture_nearest_*` — verify exact texel return, no interpolation. Extend existing `test_texture_bilinear_*` tests.
- **Rust unit tests** (`src/material/textured.rs`): `test_render_mat` already exercises the `Textured` material path with a 2×2 texture.
- **Python binding tests** (`tests/tt3de/test_r_texture_buffer.py`): `add_texture(..., filter_mode="nearest")` round-trip.
- **TTSL e2e** (`tests/tt3de/ttsl/test_e2e.py`): Verify `tt_texture` with nearest filter returns un-blended texel values.
- **Edge cases**: UV at texel boundaries (0.0, 1.0), repeat/clamp modes, power-of-two vs arbitrary dimensions, fractional UV at 0.5.

## Complexity and scope

- **Size**: Small (S). Core change is ~30 lines of new logic per `uv_map_inline`, plus plumbing.
- **Risk hotspots**: The `uv_map_inline` hot path — bilinear adds ~3 extra texel reads and ~6 lerps per sample. The branch is predictable (constant per texture). Measurable only in profiling, not expected to regress tt3de's frame time.
- **Incremental shipping**: Bilinear-only phase (already done pre-evolution) could ship independently. Filter-mode enum is the completion step.
- **Rollback**: Remove `filter_mode` parameter from `add_texture` and hardcode `Bilinear` in constructors.

## A priori performance analysis

- **Hot path**: `uv_map_inline` is called per-pixel in the material pass (post-rasterization), not in the inner triangle loop.
- **Bilinear cost**: 4 texel reads (instead of 1), ~6 `lerp_rgba` calls (4 component lerps each). No heap allocation, no branch misprediction (filter mode is constant per texture).
- **Nearest cost**: Identical to pre-evolution — single texel read plus one branch.
- **Validation**: Run the Dust demo before/after and compare frame times. Profile `cargo bench` if available.

## Risks and open questions

- **Duplicate code cleanup**: The `mod.rs` file has duplicate `impl` blocks and duplicate `parse_filter_mode` from partial edits. Needs a clean rewrite of the affected section.
- **`add_atlas_texture_from_iter` signature**: Missing `#[pyo3(signature)]` for the `filter_mode` default and may be improperly indented.
- **Default behavior change**: The pre-evolution code used nearest-neighbor. The evolution defaults to bilinear. All existing demos switch from nearest to bilinear — this is the desired behavior (fixes the Dust demo), but worth documenting.

## Decision record

- **Status**: in-progress
- **Resolution**: Implementation partially written. Core logic is sound (`FilterMode` enum, `uv_map_inline` branching, plumbing, Python binding parameter). Remaining work: clean up duplicate code blocks in `mod.rs`, add `#[pyo3(signature)]` for `add_atlas_texture_from_iter`, move `parse_filter_mode` into correct scope, fix test call sites, verify `cargo check --all-targets && cargo test && uv run maturin develop`.

## References

- `demos/3d/dust.py` — Motivation: rough underscale textures
- `src/texturebuffer/mod.rs` — `FilterMode`, `Texture`, `TextureCustom`, `uv_map_inline`, `TextureBufferPy`
- `src/texturebuffer/texture_buffer.rs` — `make_texture`, `add_texture_from_iter`, `add_atlas_texture_from_iter`
- `src/texturebuffer/atlas_texture.rs` — Atlas delegates to inner `uv_map`
- `src/material/textured.rs` — `Textured`, `BaseTexture` material renderers
- `src/ttsl/mod.rs` — `TtslTextureEnv::sample_tt_texture` trait method
- `python/tt3de/obj_loader.py` — `OBJMaterial.load_texture` (no changes needed)
- `source/low_level_api.rst` — Texture buffer documentation (to update)
