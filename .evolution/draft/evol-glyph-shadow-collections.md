---
id: evol-glyph-shadow-collections
created: 2026-05-16
authors: [franc, codex]
supersedes: []
superseded-by: ""
related:
  - demos/3d/ttsl_normal_viewpos.py
  - demos/3d/ttsl_fog_glyph_shadows.py
  - .evolution/evol-font-raster-loading-helpers.md
  - source/high_level_api.rst
  - python/tt3de/ttsl/compiler.py
---

## Summary

Several 3D TTSL demos **quantize a scalar** (diffuse + rim, fog depth, etc.) into **ordered bands** and pick a **glyph index per band** via an **if cascade** that returns `(fg, bg, glyph_index)`. Python mirrors that structure with **one `find_glyph_indices_py` call per band**, **N similarly named uniforms** (`u_g0`…`u_g3` or `u_g_hash`…), and a **`globals_dict` for `all_passes_compilation` that must stay aligned** with the shader body.

This evolution proposes a **small, explicit “glyph band collection” API** (and optional conventions) so authors declare **one ordered palette** and get **consistent register seeding + compiler metadata** without hand-copying uniform names and counts across TTSL and Python.

## Motivation and context

- **Current weakness** — The pattern is duplicated with different uniform names and thresholds:
  - `demos/3d/ttsl_normal_viewpos.py`: `shade` thresholds → `#`, `+`, `*`, `.` via `u_g_hash` … `u_g_dot`.
  - `demos/3d/ttsl_fog_glyph_shadows.py`: fog `band` thresholds → block-density glyphs via `u_g0`…`u_g3`.
- **Fragility** — Adding or reordering a band requires coordinated edits in: glyph constants, `globals_dict`, `set_variable` calls, **and** the TTSL if-ladder return indices. Easy to desync or pick glyphs whose code points **do not fit** `find_glyph_indices_py`’s `i8` encoding (already documented for `•` in `ttsl_normal_viewpos.py`).
- **Conceptual clarity** — “Glyph shadowing” here means **using glyph choice as a discrete shading channel** (halftone / stipple / density readout), not font layout. That is distinct from **sprite-sheet font loading** (see `.evolution/evol-font-raster-loading-helpers.md`), but both benefit from **declarative collections** instead of ad hoc per-demo wiring.
- **Reasoning** — A thin Python layer over existing `RegisterSettings` + compiler globals preserves TTSL expressiveness and avoids ISA/renderer changes in the first slice, while making multi-band glyph shaders easier to write and refactor.

## Goals

- Introduce a **reusable way to declare an ordered glyph band palette** (e.g. darkest → lightest, or near → far) and bind it to **uniform names the shader already uses** or to a **stable generated naming scheme** (**later API**).
- Provide helpers to:
  - resolve code points to material glyph indices with **explicit validation** for the `i8` / `find_glyph_indices_py` constraint where relevant;
  - build the **`globals_dict` fragment** for `all_passes_compilation` (types: `int` per band);
  - apply **`RegisterSettings.set_variable`** for all bands in one call (**later API**).
- Refactor at least **`ttsl_fog_glyph_shadows.py`** and **`ttsl_normal_viewpos.py`** to use the helper so the demos document the recommended pattern (**docs+demo**).
- Document when to use glyph-band collections vs one-off uniforms in `source/high_level_api.rst` or TTSL demo notes (**docs-only**).

## Non-goals

- Changing fragment output semantics, blend behavior, or how glyph indices are consumed in Rust.
- Adding TTSL **array-typed** user uniforms in phase 1 unless a separate evolution already lands array support; initial design should assume **scalar `int` per band** (current compiler/material path).
- Building a full **styling system** (themes, automatic threshold tuning, perceptual palettes).
- Replacing hand-written if-cascades inside TTSL in phase 1 (optional code generation is a later phase).

## User-visible functionality

- Demo and library authors declare something like: “this shader uses **four bands** with glyphs `▓▒░ `” or “**four bands** with `#+*.`” and pass **either** a list of uniform base names **or** adopt a **documented convention** (e.g. `u_glyph_0` … `u_glyph_{n-1}`).
- **One helper call** seeds registers and returns metadata (band count, resolved indices) for tests and docs.
- **Additive**: shaders that prefer bespoke uniform names can still be wired manually; the helper should not force a single global naming style if that blocks readability.

## Developer experience (scope discussion)

### What should feel better

1. **Single source of truth** — Order of glyphs in Python matches band order in the shader; refactors rename or reorder in one place with **fail-fast** if band count ≠ shader expectations.
2. **Discoverability** — New authors find “glyph band palette” next to other material helpers, with a **minimal worked example** mirroring the fog / normal demos.
3. **Glyph safety** — Optional **lint-time or runtime check** that every character in the palette is safe for `find_glyph_indices_py` when that path is used (surface the `•`-style footgun in the helper message, not only in a comment).

### What can remain manual (initially)

- **Threshold values** inside TTSL (`0.74`, `2.4`, etc.) stay in the shader: they are **scene- and effect-specific**. The evolution targets **palette + uniform plumbing**, not automatic quantization.
- **FG/BG colors** and logic remain in TTSL; the third tuple element is the only part the collection abstracts most directly.

### Optional later phases (clearly separated)

- **Phase 2** — Small **TTSL string snippet generator** from `(thresholds, uniform_prefix)` to emit the if-cascade; useful for long bands, but risks fighting formatter/review norms unless output is stable and readable.
- **Phase 3** — If the language gains **uniform int vectors or texture-like lookup tables** for glyph indices, revisit whether N scalars can collapse to one uniform; would be a **compiler + runtime** evolution, not just Python.

## Technical approach

- **Baseline** — `all_passes_compilation(..., globals_dict)` requires each `u_g*` key; `RegisterSettings.set_variable` seeds each; TTSL returns literal uniform-backed glyph ids in each branch.
- **Proposed change (phase 1)** — Python module under `python/tt3de/` (name TBD, e.g. `glyph_band_palette` or nested under existing materials helpers):
  - **Input**: ordered sequence of characters (or pre-resolved indices), uniform name per band (or auto names from a prefix + index).
  - **Output**: `dict` suitable for merging into `globals_dict`, plus a function `apply_to_registers(reg: RegisterSettings, ...)` or returns a forked template.
  - **Validation**: `len(names) == len(chars)`, duplicate uniform names rejected, optional `validate_i8_glyph_indices` flag.
- **Alternatives considered**
  - **Convention-only** (document `u_g0`…`u_g{n}`): zero code; rejected as sole solution — does not remove duplication or sync risk.
  - **TTSL-only macro language**: high design cost; defer.
  - **Rust-side band table**: overkill for authoring ergonomics until many materials share identical tables.
- **Affected subsystems** — Python public/helper API, two 3D demos, Sphinx high-level docs; **no** TTSL opcode or VM change for phase 1.

## Usability and documentation

- Short section in `source/high_level_api.rst`: **glyph band palettes** for “discrete glyph as shading” effects, with a link to the two demos.
- Cross-link from `.evolution/evol-font-raster-loading-helpers.md` clarifying that **font atlas loading** and **TTSL glyph-index band palettes** solve different problems but can compose (e.g. HUD uses atlas, 3D cell uses built-in glyph set).

## Testability

- Unit tests: palette of length N produces N `int` entries in the globals dict with expected keys; register application sets the same integer values as manual `set_variable` would.
- Test: invalid palette (empty, mismatched names, duplicate names) raises clear errors.
- Optional: golden comparison that refactored demos produce **identical bytecode** for unchanged shader sources (sanity that only Python wiring moved).

## Complexity and scope

- Estimated size: **S–M** for phase 1 (helper + two demo refactors + short docs).
- Risks: **over-generalizing** (parameters for thresholds, themes) before a second real adopter; keep phase 1 **data-only** (glyphs + uniform names + seeding).
- Rollback: demos revert to inline constants; helper remains unused.

## A priori performance analysis

- **Neutral** — same number of uniforms and same TTSL; only initialization-time Python changes.

## Risks and open questions

- **Uniform naming**: enforce `u_g{i}` vs allow arbitrary names — arbitrary is more readable (`u_g_hash`) but weakens generic snippet generators.
- **Interaction with `default_glyph`** — collection does not replace `ShaderPy(..., default_glyph=...)`; docs must state which band (if any) default should match.
- **Open question** — Should the helper live next to `materials` re-exports or stay in a small `tt3de.ttsl` adjunct module to avoid circular imports?

## Decision record

- **Resolution**: Pending — agree on phase-1 surface (palette + dict + register apply) and uniform naming flexibility, then implement helper + demo refactors.

## References

- `demos/3d/ttsl_normal_viewpos.py`
- `demos/3d/ttsl_fog_glyph_shadows.py`
- `.evolution/evol-font-raster-loading-helpers.md`
- `python/tt3de/ttsl/compiler.py` (`RegisterSettings`, `all_passes_compilation`)
