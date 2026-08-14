# DairyOS Execution Roadmap

_Last updated 2026-08-14. Owner: Shehryar / Trident Dairies. Maintained alongside `DairyOS_Build_Specification.md` in `docs/`, per decision D4 (spec and roadmap version with the code)._

## How to read this document

Two separate axes of work are tracked here, and they are frequently confused with each other:

**Functional completeness** — does each domain (Animals, Milk, Health, Breeding, Feeding, Workforce, Inventory, Equipment, Finance) do what a real dairy operation needs, correctly, with no silent data loss or disagreeing numbers. This is IM-013 **Phase 1**, and it is the bulk of the remaining domain work.

**Installability** — can a non-technical person on the farm install DairyOS on a machine, use it, back it up, and uninstall it cleanly, without a developer present. This is IM-013 **Phases 2 through 6**, and as of this writing almost none of it has started. The backend being functionally solid does not imply it is installable; those are genuinely different bodies of work.

Every item below carries its filed gap ID from the 10-chapter build specification (`§`) or the Phase 1 audit, so it can be cross-referenced without re-deriving scope.

---

## Phase 0 — Packaging prerequisites — DONE (2026-08-13, commit `517af5f`)

Frontend API base URL centralized (no more hardcoded hosts), TypeScript typecheck gate added to the frontend build (`tsc --noEmit && vite build`), platform-appropriate data directory resolution (`%LOCALAPPDATA%` / `Application Support` / `.local/share`, overridable), `dairyos-server` console-script CLI.

---

## Phase 1 — Functional audit and fixes

### Done this run (4 fixes, commits `9d48d8c` → `9427ab0`, 1631 → 1640 tests)

| Fix | What it corrected |
|---|---|
| Vocabulary reconciliation | Three independent copies of lifecycle_status/milking_frequency vocab disagreed; SICK dropped (health condition, not a life stage); ONCE_DAILY dropped (unsupported by sequencing) |
| G6.1 — breeding classifier unification | Three endpoints classified the same pregnancy event differently — same animal read Pregnant on one screen, Unknown on another |
| Finance ledger integrity | `payment_method` silently discarded; 4 of 6 transaction types silently uncounted; counterparty/notes collided; D2's dead code path removed |
| Finance category governance | `category` was free text while every report matched it by exact string; also fixed a live vocabulary-drift bug where the governed spelling didn't match the matching logic underneath it |
| **Equipment intelligence wiring** (this session) | Equipment status never reached the Command Center attention check at all — a payload-shape bug identical in kind to G10.4, undiscovered until now — plus the already-filed G9.1 vocabulary mismatch. Both fixed together; `POST /farm/equipment` with `OUT_OF_SERVICE` now surfaces a real attention item. |

### Not yet started — the substantial remainder

**Inventory (§8) — needs one design decision before it can be built.** The live `/farm/inventory` endpoint is event-journal-only: no queryable stock model, no balance, no reorder logic. Five separate unwired inventory designs already exist in the codebase and don't share a shape. G8.1's decision (build-spec Session 8) says stock should derive from summing RECEIVE/ISSUE movements — but the real operator form offers six movement types (PURCHASE, RECEIPT, CONSUMPTION, TRANSFER, WASTAGE, ADJUSTMENT), and which of those increase vs. decrease stock — and whether TRANSFER/ADJUSTMENT need an explicit direction or signed quantity — is a real business decision, not something to infer silently. **This needs an AskUserQuestion pass before implementation starts**, to avoid guessing wrong on money/stock-affecting logic exactly the way the finance category bug did.

**Equipment (§9) remainder.** The attention-check wiring is now fixed, but there is still no real `Equipment` entity (equipment_id, category, location, service dates, running hours) — only a free-text `equipment_id` string and an event log. `next_service_due_at` (G9.3) doesn't exist, so a MAINTENANCE-overdue check can't be built yet either.

**Health (§5).** `GET /health` is a 4-line system heartbeat, not animal data — the real surface (`HealthObservation`) has two disagreeing read paths and zero status-transition concept. Needs a real `HealthCase` entity (own `HL-YYMMDD-NNN` ID, wraps observations + diagnosis + treatments + withdrawal + resolution) per the build-spec's Session 5 decision. This is also the prerequisite for SICK returning to the lifecycle vocabulary as a proper overlay instead of a life-stage value.

**Financial intelligence (G10.4).** Two of `FinancialIntelligenceService`'s three checks are permanently unreachable — the event bridge never delivers the payload shape they read. Decided fix: rescope to a real threshold check built from actual `FinancialTransaction` rows (same data the reconciliation endpoint already reads), not invented write-path fields.

**Identity/RBAC (D3, decided 2026-08-13).** No real multi-user model exists — a single shared admin login stands in for it. Five dead identity trees are slated for deletion; a minimal Owner/Manager/Milker model needs building fresh against the existing `api/auth.py` bearer-token layer. This blocks Workforce's remaining scope (G7.2–G7.5) and is a hard prerequisite for Phase 5 (mobile/LAN exposure) below.

**Workforce (§7) remainder.** Gated on the identity rebuild above — no worker identity, no real task/schedule model behind the `pending_tasks`/`overdue_tasks`/`workload_level` fields the intelligence check already expects.

**Frontend cleanup.** `src/ui/DairyOSShell.tsx` is fully dead code — nothing live imports it, but it duplicates `App.tsx`'s entry-config and will silently drift out of sync if anyone edits the wrong file. Low effort, no dependencies; worth doing before more frontend work lands on top of it.

**Lower priority, already logged, not yet scheduled:** `severity`/`feed_type` free-text drift (opposite direction from the vocabulary bugs already fixed — accepts anything rather than rejecting typos); the extra dead Animal-adjacent code trees beyond the 5 identity ones; G6.6 (`BR-` record ID migration); G4.2 (collapse two parallel feed-entry endpoints).

### Rough sizing

Each of Inventory, Equipment-entity, HealthCase, and Identity/RBAC is a genuine feature build — new model, migration, repository, API surface, governed vocabulary, and full test coverage, in the same shape as the finance fixes but for previously-unbuilt ground rather than a bug fix. Budget one focused implementation pass per domain, with Inventory needing a decision session first.

---

## Phase 2 — SQLite support (not started)

Every migration in `db_migrations/` needs to be dual-engine safe — `op.batch_alter_table` for SQLite's lack of `ALTER COLUMN`, a test matrix running the full suite against both engines, and WAL mode + foreign-key enforcement + busy-timeout configuration for SQLite specifically (none of which Postgres needs). This is the first real gate to a single-file, no-server-required installation — Postgres requires a running service and cannot be what ships to a farm.

## Phase 3 — Backup and recovery (not started)

`VACUUM INTO` for a live-safe SQLite backup, `PRAGMA integrity_check` at backup time, and critically: `data/storage/*.json` (the operational event journal and operational-input files) are **not tracked by git and hold real farm state outside the database** — they must be in the same backup bundle as the SQLite file or a restore silently loses data the database never had. Acceptance gate: a simulated total failure where restore preserves `session_ledger` flags and NULL-vs-zero yield distinctions exactly, not approximately.

## Phase 4 — Desktop packaging (not started)

This is the phase that actually produces an installer and an uninstaller. PyInstaller for the Python backend, Tauri (~70MB, chosen over Electron's ~200MB for rural download speeds — D-PKG-2) as the desktop shell, a first-run wizard, health checks, and genuinely clean install/uninstall on Windows/macOS/Linux. Nothing here has been started; today DairyOS only runs via a developer manually starting `dairyos-server` and the Vite build on a machine with Python, Node, and a database already configured.

## Phase 5 — Mobile (not started)

PWA with offline read + queued writes, server-side reconciliation on reconnect (explicitly **not** automatic merge, D-PKG-3 — auto-merge cannot honour the milk session's uniqueness constraints or sequencing rules and would silently reintroduce the ambiguity G1.6 removed). LAN exposure is gated on real roles existing (Phase 1's identity rebuild) — `dairyos-server` already warns on stderr if bound beyond loopback today, because there is no role model yet to make that safe.

## Phase 6 — Documentation (not started)

User-facing install/operate/backup/restore documentation. Deliberately last — writing it before the mechanisms it describes exist would just mean rewriting it.

---

## Acceptance gates for "installable and uninstallable" (IM-013 §8)

- Clean install and clean uninstall on Windows, macOS, and Linux, leaving no orphaned data outside the user-chosen data directory.
- PWA verified on real Android and iOS hardware, including a deliberately out-of-sequence offline entry that must be *reported* to the operator on reconnect, never silently accepted or dropped.
- A simulated total failure (disk loss, corrupted database) where restore-from-backup preserves every integrity property the live system enforces — session ledger flags, NULL-vs-zero yield, governed vocabulary — not an approximation of them.

None of these can be evaluated meaningfully until Phases 2–4 exist; they are the finish line, not a near-term milestone.

---

## Sequencing recommendation

1. **Inventory decision session** (AskUserQuestion on movement-type direction semantics) — unblocks the highest-value remaining Phase 1 domain.
2. **Identity/RBAC rebuild (D3)** — unblocks Workforce and is a hard Phase 5 prerequisite; the earlier this lands, the fewer downstream features have to be re-touched once real users/roles exist.
3. Remaining Phase 1 domains: Inventory, HealthCase, Equipment entity, G10.4 financial intelligence, `DairyOSShell.tsx` cleanup — in roughly that order, each independently shippable and testable the way the four fixes already shipped were.
4. Phase 2 (SQLite) once Phase 1's schema is reasonably stable — every additional migration written before Phase 2 is one more migration that needs a SQLite-safe rewrite.
5. Phases 3 → 4 → 5 → 6 in order, as currently sequenced in IM-013; each depends structurally on the one before it.

This is a multi-week body of work at the pace of the fixes shipped so far, not a multi-day one. The roadmap will be re-sized as each phase's actual scope becomes concrete, the same way this session's audit re-sized Phase 1 once real code was read instead of assumed.
