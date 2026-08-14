# DairyOS Execution Roadmap

_Last updated 2026-08-14 (revised — Phase 1 status refresh). Owner: Shehryar / Trident Dairies. Maintained alongside `DairyOS_Build_Specification.md` in `docs/`, per decision D4 (spec and roadmap version with the code)._

## How to read this document

Two separate axes of work are tracked here, and they are frequently confused with each other:

**Functional completeness** — does each domain (Animals, Milk, Health, Breeding, Feeding, Workforce, Inventory, Equipment, Finance) do what a real dairy operation needs, correctly, with no silent data loss or disagreeing numbers. This is IM-013 **Phase 1**, and most of what was originally scoped is now built.

**Installability** — can a non-technical person on the farm install DairyOS on a machine, use it, back it up, and uninstall it cleanly, without a developer present. This is IM-013 **Phases 2 through 6**, and none of it has started yet. The backend being functionally solid does not imply it is installable; those are genuinely different bodies of work.

Every item below carries its filed gap ID from the 10-chapter build specification (`§`) or the Phase 1 audit, so it can be cross-referenced without re-deriving scope.

---

## Phase 0 — Packaging prerequisites — DONE (2026-08-13, commit `517af5f`)

Frontend API base URL centralized (no more hardcoded hosts), TypeScript typecheck gate added to the frontend build (`tsc --noEmit && vite build`), platform-appropriate data directory resolution (`%LOCALAPPDATA%` / `Application Support` / `.local/share`, overridable), `dairyos-server` console-script CLI.

---

## Phase 1 — Functional audit and fixes

### Done (commits `9d48d8c` → `5b14249a3`, 1631 tests, 0 warnings)

| Fix | What it corrected |
|---|---|
| Vocabulary reconciliation | Three independent copies of lifecycle_status/milking_frequency vocab disagreed; SICK dropped (health condition, not a life stage); ONCE_DAILY dropped (unsupported by sequencing) |
| G6.1 — breeding classifier unification | Three endpoints classified the same pregnancy event differently — same animal read Pregnant on one screen, Unknown on another |
| Finance ledger integrity | `payment_method` silently discarded; 4 of 6 transaction types silently uncounted; counterparty/notes collided; D2's dead code path removed |
| Finance category governance | `category` was free text while every report matched it by exact string; also fixed a live vocabulary-drift bug where the governed spelling didn't match the matching logic underneath it |
| Equipment intelligence wiring | Equipment status never reached the Command Center attention check at all — a payload-shape bug identical in kind to G10.4 — plus the already-filed G9.1 vocabulary mismatch. `POST /farm/equipment` with `OUT_OF_SERVICE` now surfaces a real attention item. |
| **G8.1 — Inventory ledger** | Built the canonical stock ledger from scratch (new model, repository, migration, `GET /farm/inventory/balance`) after an explicit decision session on movement-type direction semantics. |
| **D3 — Identity/RBAC rebuild** | Deleted 5 dead identity trees plus an orphaned `application/dashboard/` tree (28 files). Built one minimal persisted `User` table (OWNER/MANAGER/MILKER), additive to the existing env-var admin login. Unblocks Workforce and Phase 5. |
| **G5.1 — HealthCase entity** | Real status-transition entity (own `HL-YYMMDD-NNN` ID, wraps observations + diagnosis + treatments + withdrawal + resolution). `HealthObservation`/`TreatmentRecord` gained optional links; resolution is an explicit operator action only. |
| **`datetime.utcnow()` deprecation + dependency currency** | FastAPI upgraded to 0.117.0 (clears the last upstream deprecation warning); DairyOS's own `datetime.utcnow()` call sites cleaned up; forensic removal of dead root-level artifacts (`agent.py`, `dump_application.ps1`, unused root `data/database/`). Full suite now runs **0 warnings**, not just fewer. |

### Not yet started — the substantial remainder

**Equipment (§9) remainder.** The attention-check wiring is fixed, but there is still no real `Equipment` entity (equipment_id, category, location, service dates, running hours) — only a free-text `equipment_id` string and an event log. `next_service_due_at` (G9.3) doesn't exist, so a MAINTENANCE-overdue check can't be built yet either.

**Financial intelligence (G10.4).** Two of `FinancialIntelligenceService`'s three checks are permanently unreachable — the event bridge never delivers the payload shape they read. Decided fix: rescope to a real threshold check built from actual `FinancialTransaction` rows (same data the reconciliation endpoint already reads), not invented write-path fields.

**Workforce (§7) remainder.** Now unblocked — identity/RBAC (D3) is done. Still needs a real task/schedule model behind the `pending_tasks`/`overdue_tasks`/`workload_level` fields the intelligence check already expects; worker-level task assignment against the new `User` table.

**Health (§5) follow-ons, deferred when HealthCase shipped:**
- G5.6 — collapse `HealthObservation`'s two disagreeing read paths now that `HealthCase` is the real status-transition surface.
- Reintroduce SICK as a lifecycle overlay (dropped in the vocabulary reconciliation fix) now that `HealthCase` gives it somewhere real to attach to.
- Frontend UI for HealthCase — backend-only so far, no operator-facing screens yet.
- Two stray tracked `.bak` files in `src/dairyos/api/` — found during the HealthCase work, worth a cleanup pass.

**Frontend cleanup.** `src/ui/DairyOSShell.tsx` is fully dead code — nothing live imports it, but it duplicates `App.tsx`'s entry-config and will silently drift out of sync if anyone edits the wrong file. Low effort, no dependencies; worth doing before more frontend work lands on top of it.

**Lower priority, already logged, not yet scheduled:** `severity`/`feed_type` free-text drift (opposite direction from the vocabulary bugs already fixed — accepts anything rather than rejecting typos); the extra dead Animal-adjacent code trees beyond the 5 identity ones; G6.6 (`BR-` record ID migration); G4.2 (collapse two parallel feed-entry endpoints).

### Rough sizing

Equipment-entity and Workforce remainder are each a genuine feature build — new model, migration, repository, API surface, governed vocabulary, full test coverage — comparable in size to Inventory and HealthCase, which is why they're sequenced first below. G10.4 and the Health follow-ons are smaller, targeted fixes on top of existing entities. The frontend cleanup and lower-priority items are each well under a day.

---

## Phase 2 — SQLite support (not started)

Every migration in `db_migrations/` needs to be dual-engine safe — `op.batch_alter_table` for SQLite's lack of `ALTER COLUMN`, a test matrix running the full suite against both engines, and WAL mode + foreign-key enforcement + busy-timeout configuration for SQLite specifically (none of which Postgres needs). This is the first real gate to a single-file, no-server-required installation — Postgres requires a running service and cannot be what ships to a farm.

## Phase 3 — Backup and recovery (not started)

`VACUUM INTO` for a live-safe SQLite backup, `PRAGMA integrity_check` at backup time, and critically: `data/storage/*.json` (the operational event journal and operational-input files) are **not tracked by git and hold real farm state outside the database** — they must be in the same backup bundle as the SQLite file or a restore silently loses data the database never had. Acceptance gate: a simulated total failure where restore preserves `session_ledger` flags and NULL-vs-zero yield distinctions exactly, not approximately.

## Phase 4 — Desktop packaging (not started)

This is the phase that actually produces an installer and an uninstaller. PyInstaller for the Python backend, Tauri (~70MB, chosen over Electron's ~200MB for rural download speeds — D-PKG-2) as the desktop shell, a first-run wizard, health checks, and genuinely clean install/uninstall on Windows/macOS/Linux. Nothing here has been started; today DairyOS only runs via a developer manually starting `dairyos-server` and the Vite build on a machine with Python, Node, and a database already configured.

## Phase 5 — Mobile (not started)

PWA with offline read + queued writes, server-side reconciliation on reconnect (explicitly **not** automatic merge, D-PKG-3 — auto-merge cannot honour the milk session's uniqueness constraints or sequencing rules and would silently reintroduce the ambiguity G1.6 removed). LAN exposure was gated on real roles existing — that prerequisite (D3) is now done, so this phase is unblocked when its turn comes; `dairyos-server` still warns on stderr if bound beyond loopback until the LAN-exposure work itself is built.

## Phase 6 — Documentation (not started)

User-facing install/operate/backup/restore documentation. Deliberately last — writing it before the mechanisms it describes exist would just mean rewriting it.

---

## Acceptance gates for "installable and uninstallable" (IM-013 §8)

- Clean install and clean uninstall on Windows, macOS, and Linux, leaving no orphaned data outside the user-chosen data directory.
- PWA verified on real Android and iOS hardware, including a deliberately out-of-sequence offline entry that must be *reported* to the operator on reconnect, never silently accepted or dropped.
- A simulated total failure (disk loss, corrupted database) where restore-from-backup preserves every integrity property the live system enforces — session ledger flags, NULL-vs-zero yield, governed vocabulary — not an approximation of them.

None of these can be evaluated meaningfully until Phases 2–4 exist; they are the finish line, not a near-term milestone.

---

## Sequencing recommendation (revised)

1. **Equipment entity build (§9 remainder, G9.3)** — highest-value remaining Phase 1 domain build; same shape as Inventory/HealthCase (new model, migration, repository, API surface, tests), and unlocks the MAINTENANCE-overdue attention check the Command Center already has a slot for.
2. **Workforce remainder (§7)** — now unblocked by the Identity/RBAC rebuild; real task/schedule model against the new `User` table.
3. **G10.4 — Financial intelligence rescope** — smaller, targeted fix reusing existing `FinancialTransaction` data.
4. **Health follow-ons** — G5.6 (collapse the two read paths), SICK-as-overlay, HealthCase frontend UI, `.bak` file cleanup — each independently shippable, none blocking the others.
5. **Frontend cleanup** (`DairyOSShell.tsx`) and the remaining lower-priority items (vocabulary drift on `severity`/`feed_type`, `BR-` ID migration, feed-entry endpoint collapse) — low effort, slot in wherever convenient.
6. Phase 2 (SQLite) once Phase 1's schema is reasonably stable — every additional migration written before Phase 2 is one more migration that needs a SQLite-safe rewrite.
7. Phases 3 → 4 → 5 → 6 in order, as currently sequenced in IM-013; each depends structurally on the one before it.

This is a multi-week body of work at the pace of the fixes shipped so far, not a multi-day one. The roadmap will be re-sized as each phase's actual scope becomes concrete, the same way it has been re-sized twice already as real code was read instead of assumed.
