# DairyOS Canonical Capability Inventory — 2026-08-13

## Canonical line

- Canonical development branch: `recovery-execution`
- Canonical commit after this audit document: `79cdcf61e1c78f36a6e0b1b36a58f929d8dcc973`
- Canonical remote: `origin/recovery-execution`
- Local verification before the audit: `HEAD == origin/recovery-execution` at `f0395732c9ec83737da904896021fa4afa8fbb50`
- Policy: local repository is the development authority; GitHub is synchronization, backup, review, and release infrastructure.

## Branch audit

Eight pre-existing development lines were identified. A temporary `audit/canonical-2026-08-13` branch was also created during the audit and is quarantine-only; it contains no independent implementation.

| Branch | Tip before cleanup | Audit classification | Action |
|---|---|---|---|
| `recovery-execution` | `f0395732c9ec83737da904896021fa4afa8fbb50` | Canonical | KEEP |
| `sprint-039-command-center-intelligence-hardening` | `c86403f818a6bef8ac3273d7ac6af326f6f46e5b` | Fully absorbed; branch tip is an ancestor of canonical | RELEGATE / CLEAN |
| `sprint-038-api-contract-fix` | `40263d92fa563bdccbc8587be0f10a7bbb554ef5` | Divergent historical API-fix line; current canonical API/router line supersedes it | RELEGATE / CLEAN |
| `dashboard-redesign-live-kpis` | `622238a3d409fba160aae8d6b4db08077c846ba1` | Divergent historical dashboard/UI line; current Command Center/Operational UI is canonical | RELEGATE / CLEAN |
| `redesign/dairyos-operational-ui-v1` | `1aa3bdb0540bb3da91f7f6472c3179ffa69084dc` | Divergent historical operational UI redesign; superseded by current canonical UI | RELEGATE / CLEAN |
| `agent/wave-0-1-foundations` | `57a60ddde7ca41c4b59402785e8922a5c2c3df4c` | Divergent early-foundation line; current canonical architecture/data/event foundations supersede it | RELEGATE / CLEAN |
| `agent/implementation-plan-ch6-10` | `f6601e08350faa0f050da30c48d6a4b854f4b2eb` | Divergent implementation-planning/recovery line; current canonical source supersedes its scaffolding | RELEGATE / CLEAN |
| `main` | `81ced5b273777e2d777ac5ed3a1f07166bd8ce01` | Divergent default-branch history; its older workforce/event/production implementation line is superseded by canonical architecture | PRESERVE NAME; align to canonical |

## Important evidence

- `sprint-039-command-center-intelligence-hardening` was directly verified as an ancestor of canonical `f0395732`; its implementation is already represented in canonical history and must not be re-imported.
- `agent/implementation-plan-ch6-10`, `redesign/dairyos-operational-ui-v1`, and `dashboard-redesign-live-kpis` are divergent historical lines rather than descendants of the canonical commit. Their named scopes correspond to capabilities already represented in the canonical application/API/UI line.
- `main` is also divergent from canonical. Its older workforce/event/production implementation line is represented by the current canonical architecture, so its branch tip is not to be merged back.
- The canonical architecture/forensic documentation identifies the current source tree and explicitly treats recovered root-level `dairyos/` scaffolding as rejected/redundant.

## Capability preservation rule

A capability found on a stale branch is considered **already catered for** unless a direct comparison against canonical source proves a missing behavior. We do not merge stale branches wholesale and we do not revive duplicate scaffolding.

## Cleanup rule

The connected GitHub interface does not expose a branch-delete operation. Therefore redundant branch refs are to be **force-aligned to the canonical commit as quarantine/relegation**, after their pre-cleanup tip SHAs are recorded above. This removes their competing code state without losing the forensic record. `main` is aligned rather than deleted because it is the repository's default branch.

## Development rule after cleanup

1. Work only from local `D:\DairyOs` on `recovery-execution`.
2. Implement each capability once.
3. Test locally.
4. Commit locally.
5. Push to `origin/recovery-execution`.
6. Verify local `HEAD` equals `origin/recovery-execution` before beginning another capability.
7. Treat all other branches as history/quarantine, not implementation sources.

This document exists specifically to prevent repeated rediscovery and reimplementation of capabilities from historical branches.
