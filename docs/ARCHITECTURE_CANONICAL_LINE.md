# DairyOS Canonical Implementation Line

## Authority

`recovery-execution` is the canonical DairyOS implementation branch.

The authoritative runtime source tree is:

- `src/dairyos/` — Python domain, application, API, operations and infrastructure runtime.
- `src/DairyOS.Web/` — web application.

## Rules

1. New implementation work branches from `recovery-execution`.
2. Existing domain services, repositories, projections and application composition remain authoritative unless a deliberate migration replaces them.
3. One business fact has one source of truth.
4. Recovered or generated scaffolding is not promoted merely because it exists in an old archive, local recovery branch, or copied tree.
5. A root-level `dairyos/` Python package is prohibited. The canonical package location is `src/dairyos/`.
6. Historical branches and closed pull requests may be retained for auditability, but they are not alternative implementation lines.

## Recovery rule

If a recovered tree overlaps an existing canonical module, compare behavior against the canonical implementation first. Preserve the canonical implementation and recover only a specifically validated capability that is absent from it. Do not merge whole recovered directory trees.

## Current cleanup boundary

The stale Wave 0–1 pull request was closed rather than merged because its base was an older snapshot of `recovery-execution`. Its changes remain available as historical reference. Future Wave work must be re-derived against the current canonical branch rather than replaying the stale branch wholesale.
