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

## Session scope (one evolution file)

Treat each collaboration as centered on **one target** `.evolution/*.md` (the file being written or recovered). **Do not** audit or reconcile **all** evolution documents in the repo for mutual consistency unless the **user explicitly asks** (e.g. supersede chain review, roadmap alignment across proposals).

- **In scope**: internal consistency *within* that single file ([Evolution consistency (user edits)](#evolution-consistency-user-edits)); reading `source/` and materials the user links or pastes.
- **Reference mode**: only read **user-named** evolution files for tone or structure—still not a blanket cross-check of every sibling unless requested.
- **Frontmatter links** (`related`, `supersedes`): cite paths or ids as the author intends; open linked evolutions only when needed to quote accurately or honor a supersede relationship the user is discussing.

If the user switches to a different evolution path, treat that file as the new single target.

## Evolution consistency (user edits)

When the **user updates** the evolution—directly in the file, via free-text replies, or by narrowing/expanding scope—**keep the document internally consistent**:

- **Re-read** the current `.evolution/*.md` before emitting the next revision; do not assume an older in-chat snapshot is still accurate.
- **Propagate** the change across dependent sections: Summary, Goals, Non-goals, User-visible functionality, Technical approach (baseline vs phases), Complexity and scope, Testability, Performance, Risks, **Decision record**, and frontmatter (`status`, `related`, dates if policy requires).
- **Resolve contradictions**: if one section claims “docs-only” and another still describes shipped API behavior, align wording or mark deferred work explicitly.
- **Phase alignment**: sequencing bullets (e.g. doc → metadata → optional pass) should match Complexity / Testability expectations for each slice.

Treat mid-flight edits as authoritative; reconcile the whole doc rather than patching only the paragraph that changed.

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

1. Confirm entry mode (scratch / recover / reference) and the **single** target `.evolution/` filename or slug ([Session scope](#session-scope-one-evolution-file)).
2. If recover/reference: read the cited `.evolution/` files (and any linked PRs/issues if provided).
3. Summarize understanding in **≤5 lines**; ask the first 1–2 gap questions with suggestions.
4. Iterate until sections in [template.md](template.md) can be filled without hand-waving.
5. Emit or update the markdown file under `.evolution/` with complete sections; set `status` appropriately. After **user edits** to the evolution, apply [Evolution consistency (user edits)](#evolution-consistency-user-edits) before saving.
6. Apply [Git workflow (evolution commits)](#git-workflow-evolution-commits): put the change on a dedicated branch and **commit** after the file is written—unless the user explicitly asks not to commit yet.
7. Optional closing recap: one message listing **decisions**, **open risks**, and **recommended next implementation step**—each one line.

## Git workflow (evolution commits)

Evolution markdown under `.evolution/` must be committed **on its own branch**, not on the integration branch. After saving the target `.evolution/*.md`, **create a git commit** for that change (Conventional Commits, e.g. `docs: add evolution <slug>` or `docs: update evolution <slug>`).

**Branch name**: use **`evol/<evol_name>`**, matching the **`evol/<evol-description>`** branch pattern in [Git workflow — `AGENTS.md`](../../../AGENTS.md#git-workflow). Here `<evol_name>` is that description segment: usually the evolution markdown basename **without** `.md` (e.g. `evol-transparency-depth-layers.md` → `evol/evol-transparency-depth-layers`). Stay consistent with sibling `evol/*` branches; feature/chore branches remain `feat/` and `chore/` per the same section.

**Before committing**, ensure HEAD is appropriate:

| Situation | Action |
|-----------|--------|
| Current branch is **`master`** (or repo default, e.g. `main`) | `git pull` on that branch (when safe), then `git checkout -b <branch>` for this evolution, then add + commit. |
| Current branch is **unrelated** (not `master` / default, and not the branch for this evolution file) | `git checkout master` (or default), `git pull`, then `git checkout -b <branch>`, then add + commit. |
| Already on **this evolution’s branch** | Add + commit only (no new branch). |

Use the repo’s default integration branch name if it is not `master`. If checkout/pull fails (dirty tree, conflicts), stop and coordinate with the user rather than forcing.

**Anti-pattern**: committing evolution-only work directly on `master` / default while it should live on a PR branch.

## Anti-patterns

- Skipping `source/` grounding and proposing generic engine advice.
- Packing too many questions into one turn.
- Writing the final evolution file before the user confirms goal boundaries and non-goals.
- Ignoring testability or performance until the end—surface trade-offs early.
- Changing evolution doc filename conventions without matching sibling files in `.evolution/`.
- Opening or harmonizing **every** evolution in `.evolution/` when the user only asked to work on one file ([Session scope](#session-scope-one-evolution-file)).
- Updating one section after a user edit while leaving conflicting claims elsewhere (Summary vs Decision record, phases vs Non-goals, etc.).
- Saving an evolution file without moving off `master` / default when a dedicated branch is required ([Git workflow](#git-workflow-evolution-commits)).

## Verification checklist

- [ ] Read relevant `source/` pages for this topic.
- [ ] Entry mode and target path confirmed.
- [ ] All template sections addressed or explicitly marked N/A with rationale.
- [ ] Cross-section consistency checked after any user-driven scope or wording change ([Evolution consistency (user edits)](#evolution-consistency-user-edits)).
- [ ] User could implement from the doc without re-asking fundamental scope questions.
- [ ] File saved under `.evolution/` using repo-consistent naming.
- [ ] Dedicated evolution branch and commit recorded after save ([Git workflow](#git-workflow-evolution-commits)), unless the user asked to skip committing.
