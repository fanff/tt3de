---
id: evol-font-raster-loading-helpers
status: proposed
created: 2026-05-15
authors: [franc, codex]
supersedes: []
superseded-by: ""
related:
  - demos/2d/bouncing_clock.py
  - source/high_level_api.rst
  - source/low_level_api.rst
  - source/index.rst
---

## Summary

The `bouncing_clock` demo currently proves that TT3DE can render sprite-sheet glyph text through TTSL, but the demo carries too much setup boilerplate to be a good high-level example. This evolution proposes a reusable Python helper API for loading raster font glyphs from sprite sheets and materializing per-glyph render assets, then refactoring `demos/2d/bouncing_clock.py` to use that API with unchanged visual/runtime behavior.

## Motivation and context

- **Current behavior** — `bouncing_clock` manually loads a BMP sheet, slices each glyph tile, uploads one texture per sprite, forks shader register sets, and creates one shader material per sprite, all inside demo-local code.
- The amount of orchestration makes a small user-facing demo longer than necessary and hides the intended high-level workflow shown in `source/high_level_api.rst`.
- **Reference comparison** — Users typically expect text/sprite font setup to be one helper call (load atlas + mapping) plus lightweight per-instance usage, not repeated texture/material wiring in each demo.
- This change aligns with tt3de scope in `source/index.rst`: practical CPU rasterization demos with approachable Textual integration for small scenes.
- **Reasoning** — Incremental extraction into helper utilities preserves existing render semantics and avoids risky renderer changes while immediately improving ergonomics and maintainability.

## Goals

- Provide a reusable high-level Python helper for raster font glyph loading from a sprite sheet (**later API**).
- Encapsulate texture extraction/upload and glyph-to-material asset preparation for TTSL-driven glyph rendering (**later API**).
- Refactor `demos/2d/bouncing_clock.py` to consume the helper and reduce demo-local boilerplate (**docs+demo**).
- Keep runtime rendering behavior equivalent for the demo (same movement, same glyph visuals, same update cadence) (**docs+demo**).
- Document the new recommended workflow in `source/high_level_api.rst` (**docs-only**).

## Non-goals

- Changing Rust rasterization, blend model, depth handling, or shader VM execution.
- Introducing automatic transparent sorting, new glyph compositing semantics, or new material core variants.
- Designing a full text layout engine (kerning, wrapping, baseline alignment, shaping).
- Replacing existing low-level APIs; helper is additive and optional.

## User-visible functionality

- Demo authors can load a sprite-sheet-backed glyph font through a dedicated helper API instead of hand-writing tile extraction and per-glyph material setup.
- `bouncing_clock` remains visually and behaviorally equivalent, but the source code becomes shorter and easier to adapt.
- Change is additive: existing demos and low-level setup code continue to work without migration.
- Documentation clarifies when to use the helper path versus lower-level manual control.

## Technical approach

- **Baseline (current architecture)** — Python demo code does all font-sheet loading, tile extraction, texture upload, shader register seeding, material creation, and glyph lookup inline, then assigns material IDs to `TT2DUnitSquare` instances.
- **Proposed change** — Introduce a Python helper module that:
  - loads a glyph sprite sheet and mapping,
  - produces or caches per-glyph render-ready asset handles (texture/material ids),
  - exposes a simple lookup API from character/sprite to material id for demo usage.
- **Future / optional phases**
  1. Phase 1: helper extraction + `bouncing_clock` refactor + docs.
  2. Phase 2 (optional): shared caching policy across multiple views or demos in one process.
  3. Phase 3 (optional): extra convenience constructors for common monospace HUD/text widgets.
- **Alternatives considered**
  - Keep demo-local code: rejected; continues API discoverability and maintenance cost issues.
  - Move logic into Rust immediately: deferred; higher coupling and larger binding surface change than needed for first ergonomic win.
  - Add a generic text layout subsystem now: deferred; out of scope for this feedback-driven iteration.
- Affected subsystems:
  - Python high-level API layer (new helper module and docs),
  - demo code in `demos/2d/bouncing_clock.py`,
  - no expected Rust/TTSL opcode ISA changes for phase 1.
- Indicative files:
  - `python/tt3de/` (new helper module),
  - `demos/2d/bouncing_clock.py`,
  - `source/high_level_api.rst`,
  - optionally `README.md` demo notes if needed.

## Usability and documentation

- Add one canonical high-level snippet in `source/high_level_api.rst` for glyph-font helper usage in 2D demos.
- Cross-link from existing materials/TTSL sections instead of duplicating low-level details.
- Keep `bouncing_clock` as a readable reference implementation for animated text sprites.
- Document helper boundaries explicitly (it is an asset-loading convenience, not a full text layout system).

## Testability

- Python-level unit tests for helper mapping and asset construction behavior (character-to-sprite/material lookup consistency).
- Integration test path that instantiates a render context, uses helper-prepared assets, and verifies no exceptions plus stable material assignment semantics.
- Demo-level smoke run for `demos/2d/bouncing_clock.py` to confirm unchanged startup/runtime behavior.
- If helper adds caching, include tests for cache hit/miss behavior and deterministic IDs under controlled setup.

## Complexity and scope

- Estimated size: **M** (mostly Python API extraction/refactor + docs).
- Main risk hotspots:
  - preserving existing glyph visual output,
  - avoiding accidental coupling to one demo’s assumptions.
- Incremental shipping:
  - ship phase 1 alone (helper + one adopter demo + docs),
  - defer cache/system-wide convenience additions until real second adopter feedback.
- Rollback story:
  - helper is additive; if issues arise, `bouncing_clock` can temporarily revert to local setup without touching renderer internals.

## A priori performance analysis

- Hot paths for this evolution are mostly initialization-time (texture slicing/upload and material creation), not per-frame movement.
- Expected runtime impact in steady state is neutral: demo still performs per-frame transform update and occasional material-id swaps on changed digits.
- Potential benefit is reduced duplicate setup work if cache reuse is introduced later.
- Relative approach ranking (likely cheapest to most expensive):
  1. Python helper extraction with identical per-glyph assets (phase 1).
  2. Helper + per-process cache reuse across demos/views (optional phase 2).
  3. Deep Rust-side text/font subsystem introduction (deferred, highest scope/cost).
- Validation ideas:
  - compare startup cost before/after on `bouncing_clock`,
  - optional benchmark counting texture/material creations,
  - ensure no regression in frame pacing during motion/update loop.

## Risks and open questions

- API shape risk: too narrow (clock-only) versus too broad (premature generic text framework).
- Asset lifecycle ownership and cache invalidation rules need explicit definition if caching lands.
- Helper should remain transparent enough that advanced users can still drop to low-level APIs when needed.
- Open question: whether character-to-sprite mapping should rely directly on `DefaultSpriteSheet32px` or support pluggable mappings from day one.

## Decision record

- **Status**: proposed
- **Resolution**: Accepted direction for extracting reusable raster-glyph loading helpers in Python and applying them first to `bouncing_clock`, while preserving existing rendering behavior in the initial slice.

## References

- `source/index.rst`
- `source/high_level_api.rst`
- `source/low_level_api.rst`
- `demos/2d/bouncing_clock.py`
