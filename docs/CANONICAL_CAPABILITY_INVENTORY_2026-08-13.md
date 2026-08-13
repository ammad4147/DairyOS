# DairyOS Canonical Capability Inventory — 2026-08-13

## Canonical line

- Canonical development branch: `recovery-execution`
- Canonical commit: `f0395732c9ec83737da904896021fa4afa8fbb50`
- Canonical remote: `origin/recovery-execution`
- Local verification at audit start: `HEAD == origin/recovery-execution`
- Policy: local repository is the development authority; GitHub is synchronization, backup, review, and release infrastructure.

## Branch audit

The repository exposed eight pre-existing development lines plus the temporary audit branch created during this audit. The seven non-canonical development lines were compared against canonical `f0395732` and reviewed by branch purpose/commit history. No open PRs were found for the stale development lines.

| Branch | Audit classification | Action |
|---|---|---|
| `recovery-execution` | Canonical | KEEP |
| `sprint-039-command-center-intelligence-hardening` | Fully absorbed; canonical is ahead and the branch tip is an ancestor of canonical | RELEGATE / CLEAN |
| `sprint-038-api-contract-fix` | Divergent historical API-fix line; current canonical API/router line supersedes it | RELEGATE / CLEAN |
| `dashboard-redesign-live-kpis` | Divergent historical dashboard/UI line; current Command Center/Operational UI is canonical | RELEGATE / CLEAN |
| `redesign/dairyos-operational-ui-v1` | Divergent historical operational UI redesign; superseded by current canonical UI | RELEGATE / CLEAN |
| `agent/wave-0-1-foundations` | Divergent early-foundation line; current canonical architecture/data/event foundations supersede it | RELEGATE / CLEAN |
| `agent/implementation-plan-ch6-10` | Divergent implementation-planning/recovery line; current canonical source supersedes its scaffolding | RELEGATE / CLEAN |
| `main` | Divergent default-branch history; its older workforce/event/production implementation line is superseded by canonical architecture | PRESERVE NAME; align to canonical |

## Important evidence

- `sprint-039-command-center-intelligence-hardening` was directly verified as an ancestor of canonical `f0395732`; therefore its implementation is already represented in canonical history and must not be re-imported.
- The stale branches share an older common history with canonical but diverge after that point. Their existence is therefore not evidence of missing capability.
- The canonical architecture/forensic documentation identifies the current source tree and explicitly treats recovered root-level `dairyos/` scaffolding as rejected/redundant.
- Current canonical implementation includes the active application/API/UI lines that supersede the older dashboard, operational UI, API-contract, foundation, and command-center variants.

## Capability preservation rule

A capability found on a stale branch is considered **already catered for** unless a direct comparison against canonical source proves a missing behavior. We do not merge stale branches wholesale and we do not revive duplicate scaffolding.

## Cleanup rule

After this audit, redundant branch tips are to be removed from active development. Where branch deletion is unavailable through the connected GitHub operation, the branch may be force-aligned to the canonical commit as a quarantine/relegation measure, with the former tip SHA retained in this document for traceability.

## Development rule after cleanup

1. Work only from local `D:\DairyOs` on `recovery-execution`.
2. Implement each capability once.
3. Test locally.
4. Commit locally.
5. Push to `origin/recovery-execution`.
6. Verify local `HEAD` equals `origin/recovery-execution` before beginning another capability.
7. Treat all other branches as history, not implementation sources.

This document exists specifically to prevent repeated rediscovery and reimplementation of capabilities from historical branches.
