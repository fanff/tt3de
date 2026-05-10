---
name: tt3de-evol
description: >-
  Facilitates structured Q&A to author standardized tt3de evolution documents
  under `.evolution/` (versioned markdown). Reads `source/` docs for project
  context. Supports starting from scratch, recovering an incomplete evolution,
  or using an existing evolution as reference. Challenges proposals across
  functionality, technical design, usability, testability, complexity, and
  a priori performance. Use when the user mentions evolution documents,
  `.evolution/`, roadmaps, design proposals, or `/create-skill tt3de-evol`.
disable-model-invocation: true
---

# tt3de evolution documents

## Purpose

Guide collaborative writing of **evolution documents**: repo-tracked markdown files under `.evolution/` that capture **what** should change, **why**, and **how** to validate it—before or alongside implementation.

## Start here: project context

Before the first question, **read enough of `source/`** to ground suggestions in this project:

| File | Why |
|------|-----|
| [`source/index.rst`](../../../source/index.rst) | Product scope, CPU-only rasterization, Textual integration, demo entry points |
| [`source/high_level_api.rst`](../../../source/high_level_api.rst) | Public Python-facing concepts |
| [`source/low_level_api.rst`](../../../source/low_level_api.rst) | Native/binding-level surface |
| [`source/ttsl.md`](../../../source/ttsl.md) / [`source/ttsl_compiler.md`](../../../source/ttsl_compiler.md) | Shader language and compiler notes when TTSL is involved |
| [`source/opcode_reference.md`](../../../source/opcode_reference.md) | Opcode semantics when changing TTSL ISA |

Skim further `source/*.rst` / `*.md` if the evolution touches those areas. Repo-wide commands and conventions: [`AGENTS.md`](../../../AGENTS.md).

## Entry modes

Pick one at the start (confirm with the user if unclear):

1. **From scratch** — New evolution; copy structure from [template.md](template.md); choose a new slug/filename under `.evolution/`.
2. **Recover** — User points to an existing `.evolution/*.md` draft; identify empty or vague sections and drivefill them.
3. **Reference** — User names one or more existing evolutions to mirror for tone, section depth, or decision format; still tailor content to the new proposal.

If `.evolution/` is missing, create it when writing the first evolution file.

## Document standard

- One markdown file per evolution, named with a **short kebab-case slug** (example: `evol-msaa-outline.md`). Adjust naming if the repo already established a pattern—stay consistent with siblings.
- Follow section order and intent in [template.md](template.md). Frontmatter is optional but recommended for `id`, `status`, and links.

## Conversation protocol

**Cadence**: Ask **one or two** focused questions per message—never flood the user.

**Suggestions**: For each question, give a **concise suggested answer** inferred from `source/`, any referenced evolution, and the user’s stated intent.

**Replies** (same convention as [`tt3de-high`](../tt3de-high/SKILL.md)):

- **`n:y`** — Accept the suggestion for question `n`.
- **`n:n`** / **`n:no`** — Reject; offer a short alternative or ask a narrowing follow-up.
- **`n: <free text>`** — Custom answer.
- **`1:y, 2: ...`** — Batch responses in one message.

When the **AskQuestion** tool is available, present the same choices as numbered options so clicks align with `n:y`.

**Affirmation shorthand**: If the user writes **`1:y`** (or **`2:y`**), treat it as accepting that numbered suggestion for the current message’s questions.

## Challenge dimensions (cover across the session)

Ensure the evolution ends up stress-tested—not only “what we build,” but **how we know it worked** and **what it costs**. Rotate through these lenses until each is adequately addressed for this proposal:

| Lens | Challenge |
|------|-----------|
| **Functionality** | Precise behavior change, users affected, success criteria, non-goals |
| **Technical** | Subsystems, data flow, Rust/Python/TTSL boundaries, compatibility |
| **Usability** | API shape, demos, learning curve, error messages |
| **Testability** | Unit/integration/e2e coverage, regressions, TTSL opcode tests if relevant |
| **Complexity** | Scope sizing, sequencing, risky touchpoints, rollback story |
| **A priori performance** | Hot paths (per-frame, rasterization, shader VM, pyo3), allocation/branching expectations, how to measure after implementation |

For performance, stay honest: **hypotheses and guardrails**, not fake benchmarks.

## Session flow

1. Confirm entry mode (scratch / recover / reference) and target filename or slug.
2. If recover/reference: read the cited `.evolution/` files (and any linked PRs/issues if provided).
3. Summarize understanding in **≤5 lines**; ask the first 1–2 gap questions with suggestions.
4. Iterate until sections in [template.md](template.md) can be filled without hand-waving.
5. Emit or update the markdown file under `.evolution/` with complete sections; set `status` appropriately.
6. Optional closing recap: one message listing **decisions**, **open risks**, and **recommended next implementation step**—each one line.

## Anti-patterns

- Skipping `source/` grounding and proposing generic engine advice.
- Packing too many questions into one turn.
- Writing the final evolution file before the user confirms goal boundaries and non-goals.
- Ignoring testability or performance until the end—surface trade-offs early.
- Changing evolution doc filename conventions without matching sibling files in `.evolution/`.

## Verification checklist

- [ ] Read relevant `source/` pages for this topic.
- [ ] Entry mode and target path confirmed.
- [ ] All template sections addressed or explicitly marked N/A with rationale.
- [ ] User could implement from the doc without re-asking fundamental scope questions.
- [ ] File saved under `.evolution/` using repo-consistent naming.
