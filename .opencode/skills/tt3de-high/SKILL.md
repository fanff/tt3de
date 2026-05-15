---
name: tt3de-high
description: >-
  Implements high-level tt3de Python API and end-user ergonomics for Node2D,
  Node3D, Prefab, and asset loading flows (OBJ, BMP, PNG) without changing Rust
  code. Runs a design discussion first so the user drives the public interface,
  keeping the result simple, clear, and neat for project end users. Use when
  adding or changing Python scene graph helpers, prefab factories, loaders,
  convenience APIs, or high-level behavior under python/tt3de/.
---

# tt3de high-level Python work

## Scope

High-level Python-only changes under `python/tt3de/`, especially:

- `tt_2dnodes.py` / `tt_3dnodes.py` scene graph behavior (`Node2D` / `Node3D`, current `TT2DNode` / `TT3DNode` naming).
- `prefab3d.py` and `asset_fastloader.py` prefab factories (`Prefab3D`, `Prefab2D`, material/texture setup helpers).
- `asset_load.py`, `obj_loader.py`, and related Python loaders for OBJ, BMP, PNG, palette, texture, and sprite-sheet workflows.
- Public Python interfaces intended for demos, examples, and application users.

**Boundary**: do not edit Rust (`src/**.rs`) while using this skill. If the requested feature needs a native primitive, binding, hot-path optimization, or pyo3 exposure, stop and switch to [`tt3de-low`](../tt3de-low/SKILL.md) for that part.

## Contract documents

Consult these rules while designing and before implementation:

| Topic | File |
|-------|------|
| Python API conventions | [`.cursor/rules/python-standards.mdc`](../../../.cursor/rules/python-standards.mdc) |
| Scoped public API changes | [`.cursor/rules/workflow-guardrails.mdc`](../../../.cursor/rules/workflow-guardrails.mdc) |
| Test coverage expectations | [`.cursor/rules/testing-standards.mdc`](../../../.cursor/rules/testing-standards.mdc) |
| Demo-facing expectations | [`.cursor/rules/demos-standards.mdc`](../../../.cursor/rules/demos-standards.mdc) |

Repo-level platform and test commands live in [`AGENTS.md`](../../../AGENTS.md). On Windows/PowerShell, run Python tests with `$env:PYTHONPATH='.'; uv run pytest <path>`.

## Design discussion before implementation

**Do not write code until the end-user design is validated.** High-level changes define how people use tt3de, so the interface must be driven by the user's intended workflow and kept simple.

### How to ask

Present **numbered questions** with a **concise suggested answer** for each, inferred from the request and current code. Explain once how to reply:

- **`n:y`** — accept the suggestion for question `n`.
- **`n:n`** or **`n:no`** — reject the suggestion; ask a brief follow-up or offer alternatives.
- **`n: <free text>`** — custom answer for question `n`.
- Multiple lines or **`1:y, 2:y, 3: custom...`** in one message is fine.

When the **AskQuestion** tool is available, mirror the same numbered choices as clickable options. If the user already gave a clear design, still confirm it with one short recap question they can answer with `1:y`.

### Question themes (pick the subset that fits)

Use concrete suggestions grounded in the existing Python files, not generic API theory:

1. **User workflow** — What should the end user be able to write in the simplest happy path? Suggest a tiny call sequence or constructor shape.
2. **API owner** — Should the behavior live on `TT2DNode`/`TT3DNode`, `Prefab2D`/`Prefab3D`, a loader function, or a small helper module? Suggest the nearest existing owner.
3. **Naming** — Should the public name say `Node2D`/`Node3D` while preserving existing `TT2DNode`/`TT3DNode` internals, or extend current names directly? Suggest the clearest end-user name.
4. **Object shape** — Should the API return a node, prefab mesh, texture/material tuple, parsed loader data, or a small typed result object? Suggest the smallest object users need.
5. **Defaults** — What defaults make examples clean (material id, transform identity, texture alpha, triangle flipping, UV orientation, transparent colors)? Suggest explicit defaults that match current behavior.
6. **Loader input** — Should loaders accept paths, bytes, file-like objects, or all of them? Suggest one ergonomic public entry point and keep lower-level parsers reusable.
7. **PNG support** — If PNG is involved, check existing dependencies first. Do not add a runtime dependency without user approval; prefer existing project dependencies or a small stdlib-compatible path when feasible.
8. **Error behavior** — Which mistakes should raise `ValueError`, `TypeError`, or `FileNotFoundError` with actionable messages? Suggest user-facing exceptions, not silent fallbacks.
9. **Backwards compatibility** — Is this additive, or does it change a current public signature? Suggest additive wrappers unless the user explicitly wants a breaking cleanup.
10. **Docs and demos** — Should README/Sphinx docs or a demo be updated to teach the new interface? Suggest the closest user-facing example when API shape changes.
11. **Tests** — Which key behavior needs `unittest` coverage? Suggest focused unit tests for loaders, prefabs, transforms, and regression cases.

Skip irrelevant questions; do not pad the list.

## Implementation order

After the user accepts the design:

1. Update only Python files unless the user explicitly switches scope.
2. Keep public APIs typed, deterministic, and import-safe per `python-standards.mdc`.
3. Prefer small additive helpers over large refactors. Reuse existing modules instead of creating parallel utility layers.
4. Make end-user calls clear: simple names, sensible defaults, predictable return types, and specific exceptions.
5. Add or update focused tests. Prefer `unittest` style for key high-level functionality unless the surrounding test file already uses plain pytest style.
6. Update docs or demos when a public interface changes.
7. Run targeted tests with `PYTHONPATH=.`. For broad Python API work, run `uv run pytest` when practical.

## Common patterns to follow

- Use `from pyglm import glm` for GLM imports.
- Keep transforms consistent with `TT2DNode` / `TT3DNode`: local transform mutators mark global transforms dirty.
- Keep prefab helpers as factories that return ready-to-insert nodes or meshes with populated vertices, triangles, UVs, and material ids.
- Keep loader parsing separate from end-user convenience wrappers so bytes/file-like/path use cases do not duplicate parsing logic.
- Validate asset formats early and raise actionable messages such as unsupported BMP bit depth, malformed OBJ face, missing PNG support, or empty geometry.
- Preserve stable names and behavior unless the user approved a cleanup. Add aliases or convenience functions when that better serves existing users.

## Anti-patterns

- Editing Rust or pyo3 binding code under this skill.
- Designing the API around engine internals instead of the user's intended call site.
- Adding hidden global state, import-time loading, or filesystem side effects.
- Adding a runtime dependency for PNG/loading convenience without user approval.
- Returning loosely shaped tuples from new public APIs when a named object or existing class would be clearer.
- Silently changing loader orientation, UV conventions, or material defaults without tests and docs.
- Skipping discussion because the implementation looks small; high-level API names are hard to undo.

## Verification checklist

- [ ] Design discussion completed or explicitly confirmed with `1:y`.
- [ ] No Rust files edited.
- [ ] Public API is typed, simple, and end-user oriented.
- [ ] Existing Python rules followed; update `python-standards.mdc` only if a reusable convention is missing.
- [ ] `unittest` or focused tests cover key behavior and regressions.
- [ ] Docs/demos updated when public usage changed.
- [ ] Targeted `uv run pytest` command run with `PYTHONPATH=.` or limitation reported.
- [ ] Diff stays scoped to the high-level Python feature.
