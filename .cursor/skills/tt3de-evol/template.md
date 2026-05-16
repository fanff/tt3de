# Evolution: <short title>

Use this skeleton for every file under `.evolution/`. Replace angle-bracket placeholders; delete unused optional sections rather than leaving them empty.

Strong evolutions usually **name the baseline**, **contrast with a familiar reference** (e.g. OpenGL-style passes) when that prevents misunderstanding, **phase work** (document → metadata → optional heavy path), and **rank approaches by likely cost** under performance—honestly, as hypotheses not fake benchmarks.

```yaml
# Optional frontmatter (recommended for tooling and cross-links)
id: evol-<short-slug>
created: YYYY-MM-DD
authors: [<names or handles>]
supersedes: []  # list of other evolution ids this replaces
superseded-by: ""
related: []     # demos, issues, PRs, other evols
```

## Summary

One tight paragraph: what changes, for whom, and why now. If the outcome is mostly **clarity and sequencing** (default unchanged, heavy options deferred), say that upfront.

## Motivation and context

- **Current behavior** — How the pipeline works today (buffers, ordering, hot path). Point to code or `source/` pages so readers can verify.
- Problem or limitation today (symptoms, constraints).
- **Reference comparison** *(when useful)* — Contrast with an industry-default or user expectation (e.g. single depth sample + global blend vs per-cell stack). One short paragraph avoids GL/generic engine rambling.
- How this fits tt3de’s scope (CPU rasterization, Textual integration, small scenes—see `source/index.rst`).
- **Reasoning** — Why incremental change or “keep baseline + optional later path” beats a big-bang rewrite (correctness limits, ASCII final cell, etc.).

## Goals

Bullet list of concrete outcomes. Verifiable where possible. When work spans phases, tag bullets (**docs-only**, **later API**, **opt-in behavior**) so scope stays honest.

## Non-goals

Explicit boundaries and deferred work. Call out correctness limits users should not expect (e.g. intersecting transparency, sort-key approximation).

## User-visible functionality

- What users (library consumers or demo authors) can do after this evolution.
- Breaking vs additive behavior; migration notes if any.
- If only documentation changes first, state explicitly that runtime behavior is unchanged for that phase.

## Technical approach

Structure this section so implementers see **today vs tomorrow**:

- **Baseline (current architecture)** — Submission order, buffer flows, resolve rules—facts, not proposals.
- **Proposed change** — What actually changes in code or docs for this evolution’s shipped slice.
- **Future / optional phases** — Heavier or riskier pieces deferred; numbered steps welcome when order matters.
- **Alternatives considered** — Short reject/defer list with one-line rationale each (cost, wrong for intersections, scope).
- Affected subsystems (Rust core, Python API, TTSL/shaders, build/docs).
- Files or modules likely touched (indicative, not a promise).

## Usability and documentation

- Public API / demo ergonomics.
- Docs to update (`source/`, `README`, opcode reference if TTSL changes).
- Prefer **one canonical deep dive** plus **cross-links** from high-level pages so the mental model is discoverable.

## Testability

- Unit vs integration vs visual/e2e expectations.
- Concrete cases and edge cases to lock in.
- Existing test files or patterns to extend.

## Complexity and scope

- Estimated size (S/M/L) and risk hotspots.
- Dependencies between tasks; **what can ship incrementally** (e.g. docs alone, then metadata, then optional second pass).
- Rollback story if something lands behind a flag.

## A priori performance analysis

- Hot paths (per-frame, per-triangle, shader VM, Python boundary).
- Expected allocation / branching / cache behavior.
- **Relative ranking** *(when comparing approaches)* — Ordered list from likely-cheapest to likely-most-expensive for tt3de-scale workloads (hypotheses; validate after implementation).
- How to validate later (benchmark ideas, profiling hooks, demo stress cases).

## Risks and open questions

- Known unknowns, compatibility worries, security or correctness traps.
- Approximations users might assume are exact (sort keys, layer caps, material writes).

## Decision record

- **Resolution**: one paragraph once decided (fill when closing the evolution). Track lifecycle by moving the file between `.evolution/draft/`, `.evolution/done/`, and `.evolution/to_implement/` rather than encoding state in the body.

## References

- Links to prior evolutions, issues, PRs, and canonical docs under `source/`.
