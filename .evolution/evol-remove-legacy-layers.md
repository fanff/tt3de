# Evolution: Remove legacy `legacy_layers` compatibility path

```yaml
id: evol-remove-legacy-layers
status: proposed
created: 2026-05-14
updated: 2026-05-14
authors: []
supersedes:
  - evol-transparency-depth-layers
superseded-by: ""
related:
  - .evolution/evol-transparency-depth-layers.md
  - src/drawbuffer/mod.rs
  - src/drawbuffer/drawbuffer.rs
  - src/raster/mod.rs
  - src/primitiv_building/mod.rs
  - python/tt3de/render_context_rust.py
  - source/low_level_api.rst
  - source/high_level_api.rst
```

## Summary

Remove the temporary `legacy_layers=True` compatibility mode and make the two-pass architecture the only rendering path.

After this evolution, `DrawingBufferPy` no longer exposes the legacy `DrawBuffer<2, f32>` flow. The engine always renders using:

1. opaque pass (`DrawBuffer<1, f32>`, depth write on),
2. transparent pass (`DrawBuffer<1, f32>`, depth write off),
3. transparent front-color compositing with `BlendMode` and `GlyphPolicy`.

## Motivation and context

`legacy_layers` was introduced as a migration bridge while moving from K-buffer-like layering to explicit opaque + transparent passes. It has now served its purpose:

- It adds maintenance overhead (dual codepaths in Rust and Python).
- It complicates tests and docs with branch-specific behavior.
- It slows feature work because every rendering change must preserve obsolete semantics.

Keeping both paths increases risk of regressions and API confusion. Removing `legacy_layers` consolidates behavior and simplifies future transparency work.

## Goals

- Remove `legacy_layers` argument and internal branching from `DrawingBufferPy`.
- Remove legacy `DrawBuffer<2, f32>` usage in runtime render flow.
- Keep public transparency workflow stable (`transparent` primitive flag, per-material `blend_mode`, `glyph_policy`).
- Update docs and tests to reflect one canonical rendering model.

## Non-goals

- Introducing transparent primitive sorting in this milestone.
- Changing `BlendMode` equations or adding new blend variants.
- Changing default `transparent=False` primitive qualification semantics.

## User-visible functionality

- **Breaking change:** `DrawingBufferPy(..., legacy_layers=...)` is removed.
- Default behavior becomes the current `legacy_layers=False` path.
- Any code relying on old layered depth stack behavior is no longer supported.

## Technical approach

### 1. Remove legacy fields and branches

- In `src/drawbuffer/mod.rs`, remove:
  - `legacy_layers` state,
  - legacy `db: DrawBuffer<2, f32>` runtime dependency,
  - conditional branches selecting legacy vs new path.
- Keep only:
  - `opaque_db: DrawBuffer<1, f32>`,
  - `transparent_db: DrawBuffer<1, f32>`.

### 2. Normalize render pipeline calls

- In `src/raster/mod.rs`, keep pass-filtered raster API as the sole path.
- In `src/primitiv_building/mod.rs`, keep:
  - opaque material resolve on `opaque_db`,
  - transparent composite from `transparent_db` to opaque canvas.
- In `python/tt3de/render_context_rust.py`, remove conditional flow and always execute dual pass.

### 3. Remove compatibility/deprecation behavior

- Delete deprecation warning logic tied to `legacy_layers=True`.
- Remove mention of transitional compatibility in constructor docstrings and comments.

### 4. Cleanup and simplify tests

- Update tests to assert only single-pass-per-buffer semantics (`L=1` per pass).
- Remove tests that explicitly exercise legacy layered resolve behavior.

## Usability and documentation

- Update `source/low_level_api.rst` to remove compatibility narrative and present only the dual-pass model.
- Update `source/high_level_api.rst` examples so they do not mention `legacy_layers`.
- Add a concise migration note:
  - remove `legacy_layers` kwargs from user code,
  - validate scenes that previously depended on two-layer stacking artifacts.

## Testability

- Rust:
  - `cargo check --all-targets`
  - `cargo test`
  - drawbuffer/raster/material tests updated for single canonical path.
- Python:
  - `$env:PYTHONPATH='.'; uv run pytest`
  - targeted coverage for transparent pass behavior and blend dispatch.

## Complexity and scope

- Scope: medium.
- Estimated touchpoints:
  - `src/drawbuffer/mod.rs`
  - `src/primitiv_building/mod.rs`
  - `src/raster/mod.rs`
  - `python/tt3de/render_context_rust.py`
  - relevant tests and docs.
- Primary risk is test churn and accidental reliance on legacy buffer assumptions.

## Risks and open questions

- Some demos/tests may still implicitly depend on historical two-layer behavior.
- Removal should be coordinated with a short migration note in release/changelog.
- If any consumer still requires legacy behavior, they should pin to the prior release rather than preserving dual runtime paths.

## Decision record

- **Status:** proposed
- **Resolution target:**
  1. Remove `legacy_layers` API and implementation branches.
  2. Keep dual-pass `DrawBuffer<1, f32>` architecture as the only supported path.
  3. Update tests/docs in the same PR.

## References

- `.evolution/evol-transparency-depth-layers.md`
- `src/drawbuffer/mod.rs`
- `src/drawbuffer/drawbuffer.rs`
- `src/raster/mod.rs`
- `src/primitiv_building/mod.rs`
- `python/tt3de/render_context_rust.py`
