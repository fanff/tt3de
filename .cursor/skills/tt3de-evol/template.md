# Evolution: <short title>

Use this skeleton for every file under `.evolution/`. Replace angle-bracket placeholders; delete unused optional sections rather than leaving them empty.

```yaml
# Optional frontmatter (recommended for tooling and cross-links)
id: evol-<short-slug>
status: draft   # draft | proposed | accepted | superseded
created: YYYY-MM-DD
authors: [<names or handles>]
supersedes: []  # list of other evolution ids this replaces
superseded-by: ""
related: []     # demos, issues, PRs, other evols
```

## Summary

One tight paragraph: what changes, for whom, and why now.

## Motivation and context

- Problem or limitation today (symptoms, constraints).
- How this fits tt3de’s scope (CPU rasterization, Textual integration, small scenes—see `source/index.rst`).

## Goals

Bullet list of concrete outcomes. Verifiable where possible.

## Non-goals

Explicit boundaries and deferred work.

## User-visible functionality

- What users (library consumers or demo authors) can do after this evolution.
- Breaking vs additive behavior; migration notes if any.

## Technical approach

- Affected subsystems (Rust core, Python API, TTSL/shaders, build/docs).
- Main design choice and alternatives considered (short).
- Files or modules likely touched (indicative, not a promise).

## Usability and documentation

- Public API / demo ergonomics.
- Docs to update (`source/`, `README`, opcode reference if TTSL changes).

## Testability

- Unit vs integration vs visual/e2e expectations.
- Concrete cases and edge cases to lock in.
- Existing test files or patterns to extend.

## Complexity and scope

- Estimated size (S/M/L) and risk hotspots.
- Dependencies between tasks; what can ship incrementally.

## A priori performance analysis

- Hot paths (per-frame, per-triangle, shader VM, Python boundary).
- Expected allocation / branching / cache behavior.
- How to validate later (benchmark ideas, profiling hooks, demo stress cases).

## Risks and open questions

- Known unknowns, compatibility worries, security or correctness traps.

## Decision record

- **Status**: draft | proposed | accepted | superseded
- **Resolution**: one paragraph once decided (fill when closing the evolution).

## References

- Links to prior evolutions, issues, PRs, and canonical docs under `source/`.
