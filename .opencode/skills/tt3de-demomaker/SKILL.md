---
name: tt3de-demomaker
description: >-
  Adds or edits runnable tt3de demos under demos/ using Textual and TT3DViewStandAlone,
  including TTSL ShaderPy materials, 2D/3D scene graphs, textures, and camera setup.
  Runs a short discovery pass first (what to showcase, 2d vs 3d, TTSL vs geometry, etc.) with
  suggested answers the user can accept via shorthand. Use when the user asks for a demo,
  example app, standalone viewer, or demos/2d or demos/3d scripts.
---

# tt3de demomaker

## Scope

Orchestrate **new or edited demos** in `demos/`: run discovery, then implement following repo rules.

**Technical** (layout, ShaderPy, scene graph, textures, docstrings, comments, checklist): `.cursor/rules/demos-standards.mdc` (globs `demos/**/*.py`). **General Python**: `.cursor/rules/python-standards.mdc`.

**TTSL** (language, compiler, opcodes, ABI): `.opencode/skills/ttsl-implementation/SKILL.md`, plus `source/ttsl.md` and `source/ttsl_compiler.md`.

**Textual-heavy demos** (especially `demos/ttsl.py`): `.cursor/rules/textual-ui-helper.mdc`.

## Discovery before implementation

**Do not write or edit demo code until discovery is settled.** First surface what the demo should **showcase** (one primary teaching goal) and any **implementation specifics** (dimensionality, animation, TTSL vs static materials, textures, camera, interaction, filename/location).

### How to ask

Present **numbered questions**. After each question, give a **concise suggested answer** tailored to what the user already said (infer reasonable defaults when silent). Explain once how to reply:

- **`n:y`** — accept the suggestion for question `n` (yes / use default).
- **`n:n`** or **`n:no`** — reject the suggestion for question `n`; the agent asks a brief follow-up or offers alternatives.
- **`n: <free text>`** — custom answer for question `n`.
- Multiple lines or **`1:y, 2:y, 3: custom...`** in one message is fine.

When the **AskQuestion** tool (or equivalent structured UI in the agent harness) is available, map the same numbered options into it so the user can click choices instead of typing shorthand—keep wording aligned with the markdown suggestions.

If the user already stated goals unambiguously in their latest message, **still confirm** with one short recap question or a single numbered checklist they can answer with `1:y` to proceed.

### Typical question themes (examples only)

Use a subset that fits the request: primary showcase, 2D vs 3D, static vs animated, TTSL entry vs no shader, textures/assets, camera framing, demo path (`demos/2d` vs `demos/3d`), and whether to mirror an existing demo.

## After discovery

Implement against `.cursor/rules/demos-standards.mdc` and `.cursor/rules/python-standards.mdc`. Use the **Checklist** at the bottom of `demos-standards.mdc`, and confirm discovery is settled (or explicitly waived with `1:y`-style confirmation to proceed).

Do not attempt to run the demo; since it's a TUI application, you are going to have problems running it.
If you need validation, ask the user to run the demo and report results.
