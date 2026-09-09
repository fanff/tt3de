---
name: tt3de-demomaker
description: >-
  Adds or edits runnable tt3de demos under demos/ using Textual and TT3DViewStandAlone:
  app skeleton, scene graph, ShaderPy wiring, textures, and camera setup. Does not
  author TTSL shader source—delegates SHADER_SRC to ttsl-implementation. Runs a short
  discovery pass first with suggested answers the user can accept via shorthand. Use
  when the user asks for a demo, example app, standalone viewer, or demos/2d or demos/3d
  scripts.
disable-model-invocation: true
---

# tt3de demomaker

## Scope

Orchestrate **new or edited demos** in `demos/`: run discovery, then implement **Python demo plumbing** following repo rules.

You **own:** Textual app shell, `TT3DViewStandAlone` lifecycle, scene graph, camera, texture registration, material slot 0 sentinel, `all_passes_compilation` / `ShaderPy` / `set_shader_time` **wiring**, module docstrings, and demo checklists.

You **do not own:** contents of `SHADER_SRC` (the TTSL function bodies), TTSL language fixes, compiler opcodes, Cranelift lowering, or `source/ttsl.md` semantics. For any of that, **delegate** to [ttsl-implementation](../ttsl-implementation/SKILL.md) (invoke that skill or ask the user to run it)—do not draft or “quick fix” TTSL yourself.

**Technical** (layout, ShaderPy integration patterns, checklist): [.cursor/rules/demos-standards.mdc](../../../.cursor/rules/demos-standards.mdc) (globs `demos/**/*.py`). **General Python**: [.cursor/rules/python-standards.mdc](../../../.cursor/rules/python-standards.mdc).

**Textual-heavy demos** (especially `demos/ttsl.py`): [.cursor/rules/textual-ui-helper.mdc](../../../.cursor/rules/textual-ui-helper.mdc).

Read `source/ttsl.md` / `source/ttsl_compiler.md` only when wiring uniforms or choosing static vs shader materials—not to invent shader algorithms.

## TTSL delegation (required)

| You may | You must not |
|---------|----------------|
| Decide *whether* the demo uses `ShaderPy` vs static materials | Write or rewrite `SHADER_SRC` lines (entry function, builtins, math, transparency) |
| Pass `SHADER_SRC` into `all_passes_compilation` after the TTSL skill supplies it | Patch compile errors by editing TTSL “just enough to compile” |
| Wire `globals_dict`, `register_seed`, `ssa_json`, `time_f32_reg`, `set_shader_time` | Add opcodes, edit `compiler.py`, `low_level_def.py`, or `ir_lower.rs` |
| Copy an **existing** demo’s `SHADER_SRC` unchanged when mirroring that demo | Invent new TTSL beyond what **ttsl-implementation** produced |

**Workflow when the demo needs custom shading:**

1. Finish discovery (include a short **shader intent** brief: inputs, effect, animated or not).
2. **Stop** before filling `SHADER_SRC`, or leave a clearly marked placeholder.
3. **Delegate:** invoke [ttsl-implementation](../ttsl-implementation/SKILL.md) with the intent, entry function name, and required `globals_dict` keys; integrate the returned source.
4. If compilation fails or behavior is wrong in the shader, **do not edit TTSL**—tell the user to run **ttsl-implementation** again (or switch to that skill) with the error / desired fix.

**User-facing message template** (adapt, do not parrot):

> This demo needs TTSL shader source. Use the **ttsl-implementation** skill (or @-mention it) to write/fix `SHADER_SRC` for `<entry_fn>` with `<brief intent>`. I can wire `ShaderPy`, scene graph, and textures once the shader compiles.

## Discovery before implementation

**Do not write or edit demo code until discovery is settled.** First surface what the demo should **showcase** (one primary teaching goal) and any **implementation specifics** (dimensionality, animation, shader vs static materials, textures, camera, interaction, filename/location).

When shading is TTSL-based, capture **shader intent** in discovery (uniforms, varyings, effect)—that brief goes to **ttsl-implementation**, not into improvised `SHADER_SRC` in this skill.

### How to ask

Present **numbered questions**. After each question, give a **concise suggested answer** tailored to what the user already said (infer reasonable defaults when silent). Explain once how to reply:

- **`n:y`** — accept the suggestion for question `n` (yes / use default).
- **`n:n`** or **`n:no`** — reject the suggestion for question `n`; the agent asks a brief follow-up or offers alternatives.
- **`n: <free text>`** — custom answer for question `n`.
- Multiple lines or **`1:y, 2:y, 3: custom...`** in one message is fine.

When the **AskQuestion** tool (or equivalent structured UI in the agent harness) is available, map the same numbered options into it so the user can click choices instead of typing shorthand—keep wording aligned with the markdown suggestions.

If the user already stated goals unambiguously in their latest message, **still confirm** with one short recap question or a single numbered checklist they can answer with `1:y` to proceed.

### Typical question themes (examples only)

Use a subset that fits the request: primary showcase, 2D vs 3D, static vs animated, **shader intent** (for ttsl-implementation) vs no shader, textures/assets, camera framing, demo path (`demos/2d` vs `demos/3d`), and whether to mirror an existing demo (reuse its `SHADER_SRC` verbatim only when mirroring).

## After discovery

Implement against [.cursor/rules/demos-standards.mdc](../../../.cursor/rules/demos-standards.mdc) and [.cursor/rules/python-standards.mdc](../../../.cursor/rules/python-standards.mdc). Use the **Checklist** at the bottom of `demos-standards.mdc`, and confirm discovery is settled (or explicitly waived with `1:y`-style confirmation to proceed).

If `SHADER_SRC` is still missing, complete all non-TTSL wiring and block on **ttsl-implementation** rather than writing placeholder shader logic beyond `pass`-level stubs.

Do not attempt to run the demo; since it's a TUI application, you are going to have problems running it.
If you need validation, ask the user to run the demo and report results.

## Verification checklist (demomaker)

- [ ] Discovery settled; shader intent documented if using `ShaderPy`
- [ ] `SHADER_SRC` authored by **ttsl-implementation** (or copied unchanged from an existing demo being mirrored)
- [ ] No TTSL edits made in this skill for compile fixes or effect tweaks
- [ ] Slot-0 static material, `ShaderPy` with `ssa_json` / `register_seed`, `globals_dict` / `set_shader_time` wired per demos-standards
- [ ] Module docstring with **Run:** line; user asked to run TUI if validation needed
