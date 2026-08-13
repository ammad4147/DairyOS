# IM-013 — DairyOS Product Consolidation and Distribution Plan

**Document ID:** IM-013
**Version:** 1.0
**Status:** Proposed — awaiting approval
**Related:** AA-013 (Operator Interface Design), TA-005 (Database Technology), TA-009 (Deployment Architecture), DR-001 (Backup and Disaster Recovery)

---

# 1. Purpose

DairyOS is currently a source tree that a developer can run. This document is
the plan to make it a **product**: installable on a farm PC, usable from a
phone in the barn, and recoverable in full after a total failure.

It covers the analysis of the current state, the four architectural decisions
taken, the phased implementation plan, and the acceptance tests that decide
whether the work is finished.

---

# 2. Current State — Findings

Established by direct inspection of the codebase on 2026-08-13.

## 2.1 The schema is already database-portable

**No PostgreSQL-specific types are used anywhere.** No `JSONB`, no `ARRAY`, no
`sqlalchemy.dialects` imports. Every model uses generic types: `JSON`, `Text`,
`String`, `Float`, `Integer`, `DateTime`, `Date`, `Boolean`.

The connection string is already resolved from `DAIRYOS_DATABASE_URL` or
`DAIRYOS_DB_*` environment variables through a single module
(`data/database/session.py`), with no credentials in source.

A residual SQLite `event_journal` exists at `src/DairyOS.Web/dairyos.db`,
confirming SQLite has been exercised previously.

**Consequence:** supporting SQLite is a modest, bounded piece of work rather
than a rewrite. This finding is what makes the rest of the plan affordable.

## 2.2 The dependency set is small and bundle-friendly

`fastapi`, `sqlalchemy`, `alembic`, `psycopg[binary]`, `pydantic`,
`python-dotenv`, `uvicorn`. No numpy, no pandas, no native extensions beyond
psycopg. Python 3.12 minimum. 2,186 Python files.

**Consequence:** a PyInstaller bundle of the backend is realistic at roughly
40–60MB.

## 2.3 Backup today is PostgreSQL-only

`scripts/database_backup.py` and `data/database/backup.py` both shell out to
`pg_dump` / `pg_restore` and explicitly reject non-PostgreSQL URLs. They verify
a dump by listing it with `pg_restore --list`, which is sound practice.

**Consequence:** a SQLite backup path must be built, and the backup service
must dispatch on dialect.

## 2.4 Blocking gaps

| Gap | Detail | Blocks |
|---|---|---|
| Hardcoded API host | `localhost:8000` literal in **7** frontend files; only `tabStateClient.ts` and `farmIntelligenceClient.ts` honour `VITE_DAIRYOS_API_URL` | Packaging, all mobile |
| No server entrypoint | No `uvicorn.run` anywhere; there is no way to start DairyOS *as an application* | Packaging |
| No `tsconfig.json` | `build` is bare `vite build` — esbuild transpile only, never typechecked | Safe distribution |
| Storage files outside the DB | `data/storage/*.json` hold real operational state and are not covered by any database backup | Recovery correctness |
| No roles | `api/auth.py` issues signed bearer tokens, but **five unwired identity trees** exist and none is imported by any router (per D3: delete all five, design fresh) | Mobile — LAN exposure |

---

# 3. Decisions of Record

Taken 2026-08-13.

| # | Decision | Rationale |
|---|---|---|
| D-PKG-1 | **SQLite is the default for the packaged single-farm application; PostgreSQL remains supported** via `DAIRYOS_DATABASE_URL` | One file makes backup, verification and total-failure recovery genuinely trustworthy; no database service to install, supervise or repair on a farm PC |
| D-PKG-2 | **Tauri** as the desktop shell | ~70MB installer against Electron's ~200MB, and materially lower memory on old hardware. Chosen because farms download over poor rural connections |
| D-PKG-3 | Mobile is **offline read plus queued writes with server-side reconciliation** | Automatic merge cannot honour the session ledger's uniqueness and sequencing rules; it would resolve conflicts by overwriting and silently reintroduce the ambiguity G1.6 removed |
| D-PKG-4 | The five prerequisites are done **now, before the AA-013 dashboard build** | They are roughly a day's work and everything downstream assumes them; retrofitting a configurable API into a finished dashboard is strictly more expensive |

## 3.1 Accepted costs

**D-PKG-1** requires the three Alembic migrations to use
`op.batch_alter_table`, since SQLite cannot `ALTER COLUMN` directly. It also
introduces a dual-database test matrix. SQLite serialises writes; at
single-farm concurrency (a handful of operators) this is not a practical
limit, but it is a real ceiling that a multi-site deployment would hit — which
is why PostgreSQL support is retained rather than dropped.

**D-PKG-2** adds a Rust toolchain to the build chain and a less familiar
debugging story than Electron. The backend sidecar is the dominant complexity
either way, so this cost is smaller than it first appears.

**D-PKG-3** means the barn experience is honest rather than seamless. An
operator will sometimes see "4 of 6 entries synced — 2 need your attention".
That is the correct trade: the alternative is a ledger nobody can trust.

---

# 4. Target Architecture

## 4.1 Desktop

```
┌─────────────────────────────────────────────┐
│  Tauri shell (OS webview)                   │
│  ├── DairyOS.Web (React SPA, built)         │
│  └── sidecar: dairyos-server (PyInstaller)  │
│        └── FastAPI + uvicorn                │
│              └── SQLite (WAL) — one file    │
└─────────────────────────────────────────────┘
        │ binds 127.0.0.1 by default
        │ binds 0.0.0.0 when LAN mode enabled
        ▼
   Phones on the farm LAN (PWA)
```

The shell owns the sidecar lifecycle: start on launch, health-check before
showing the UI, stop on quit, and surface a readable error if the backend
fails rather than an empty white window.

## 4.2 Data directories

Resolved per-platform, never inside the install directory, so that
uninstalling the application cannot delete the farm's data.

| Platform | Data root |
|---|---|
| Windows | `%LOCALAPPDATA%\DairyOS` |
| macOS | `~/Library/Application Support/DairyOS` |
| Linux | `~/.local/share/DairyOS` |

```
DairyOS/
├── dairyos.db          # the database
├── storage/            # operational state JSON (§2.4)
├── backups/            # versioned restore points
├── logs/
└── config.json         # farm name, units, currency, backup target
```

The backup location is user-configurable at first run and may point at an
external drive or network path.

## 4.3 Mobile

The same React SPA, served by the farm PC, installed to the phone home screen
as a PWA. A service worker caches the shell and reference data for offline
viewing. Writes made offline enter a local queue and are replayed on reconnect
through the normal governed endpoints.

---

# 5. Backup and Recovery Design

This is requirement C and the part of the plan with the least tolerance for
being approximately right.

## 5.1 Principles

- **A backup that has not been restored is not a backup.** Verification is part
  of taking one, not part of using one.
- **The whole data set, not only the database.** `storage/*.json` and
  `config.json` are included; a database-only backup is incomplete (§2.4).
- **Restore points, not a single file.** A corruption discovered on Thursday
  must be recoverable from Tuesday.

## 5.2 Mechanism (SQLite)

| Concern | Approach |
|---|---|
| Consistent snapshot | `VACUUM INTO '<target>'` — a clean copy taken with the application running, not a file copy of a live WAL database |
| Verification | `PRAGMA integrity_check` on the copy, plus schema-version and row-count sanity checks, before the backup is recorded as valid |
| Bundle | Database snapshot + `storage/` + `config.json` + a manifest (timestamp, app version, schema revision, row counts, checksum) |
| Retention | Versioned and time-tiered: keep N daily, N weekly, N monthly |
| Restore | Verify → stop writes → move current aside (never delete) → swap in → restart → post-restore integrity check |

PostgreSQL deployments keep the existing `pg_dump` / `pg_restore` path. The
backup service dispatches on dialect behind one interface.

## 5.3 Triggers

- **Scheduled** — daily, at a configurable time.
- **Event-driven** — on significant operational events: all milking sessions
  for a day settled, month-end close, before any schema migration.
- **Manual** — a one-click backup from the UI, with visible progress and an
  explicit success or failure result.

## 5.4 Backup targets

Defined behind a `BackupTarget` interface from the start so the architecture
permits growth without rework:

| Target | First release |
|---|---|
| Local directory | Yes |
| External drive | Yes |
| Network path (SMB/NFS) | Yes |
| Cloud object storage | Interface only |

## 5.5 Restore experience

One screen listing restore points with timestamp, size, app version and
verification status. Selecting one shows what it contains — animals, milk
records, date range — **before** anything is overwritten. The current database
is moved aside, never deleted, so a restore can itself be undone.

---

# 6. Implementation Plan

Six phases. Phase 0 runs now per D-PKG-4; phases 2 onward follow the AA-013
dashboard build and the functional audit.

## Phase 0 — Prerequisites (before AA-013)

**Roughly one day. Everything downstream assumes it.**

1. Single API base-URL module in the frontend, resolved from
   `VITE_DAIRYOS_API_URL` with a sensible default. Remove all seven hardcoded
   literals.
2. `dairyos.server:main` entrypoint — `uvicorn.run` with configurable host,
   port and data directory.
3. `tsconfig.json` plus `tsc --noEmit && vite build` as the build script.
4. Data-directory resolution module: platform-correct paths, overridable by
   environment variable.

**Exit:** the frontend talks to a configurable host; the backend starts with
one command; the frontend typechecks; nothing is written inside the source tree.

## Phase 1 — Functional audit and fixes

Full functional audit across all modules, then fixes. Placeholder and
incomplete features are either finished or explicitly marked as unavailable —
per AA-013 §2.1, a feature that silently does nothing is worse than one that
says it is not ready.

This phase also clears the AA-013 blockers: lifecycle vocabulary
reconciliation, breeding classifier unification (G6.1), and the missing animal
retirement path.

## Phase 2 — SQLite support

1. Migrations converted to `op.batch_alter_table`; verified on empty,
   `create_all`, re-run and full downgrade→upgrade cycles on **both** engines.
2. Dual-database test matrix — the full suite green on SQLite and PostgreSQL.
3. WAL mode, foreign keys and busy-timeout configured.
4. Partial unique index confirmed effective on SQLite (`sqlite_where` is
   already present on the model).

**Exit:** 1,596-plus tests pass against both engines; a farm can run on either.

## Phase 3 — Backup and recovery

Built per §5, ahead of packaging, because an installer that ships without
recovery is the one thing that cannot be fixed after the fact.

**Exit:** the simulated-total-failure drill in §8 passes.

## Phase 4 — Desktop packaging

1. PyInstaller bundle of the backend.
2. Tauri shell with sidecar lifecycle management and a readable failure state.
3. Installers: NSIS (Windows), dmg (macOS), AppImage and deb (Linux).
4. Uninstaller that removes the application and **asks separately** about farm
   data, defaulting to keeping it.
5. Versioning and the Tauri updater, with a documented manual update path for
   farms with no internet.
6. First-run wizard: farm name, units, currency, timezone, data directory,
   backup location, first admin account.
7. System health checks: database integrity, disk space, backup age and status.

**Exit:** clean install and uninstall verified on all three platforms.

## Phase 5 — Mobile

1. Responsive layouts for the AA-013 sections, prioritising the barn workflows:
   herd and milk status, recording yields, receiving findings, basic entry.
2. PWA manifest, service worker, installability.
3. LAN mode: opt-in binding beyond localhost, with discovery instructions.
4. **Identity and roles (G7.1)** — delete the five dead trees per D3, then
   build fresh. This gates LAN exposure and is not optional.
5. Offline queue and reconciliation per D-PKG-3, including the sync-results
   screen.

**Exit:** the acceptance tests in §8.

## Phase 6 — Documentation and consolidation

Installation, uninstallation, backup and restore, mobile access, updating,
and a first-run guide. Written for a farm manager, not a developer.

---

# 7. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| SQLite migration surfaces hidden dialect assumptions | Phase 2 overruns | Dual-engine test matrix from the first commit of the phase, not at the end |
| Offline reconciliation UX is confusing in the barn | Operators stop trusting sync | Ship offline **read** first; add queued writes once the sync-results screen has been tested with a real operator |
| Tauri sidecar lifecycle on Windows | App appears to hang at launch | Health-check with timeout before showing the UI; explicit failure screen; never a blank window |
| macOS and Windows code signing | Installers blocked or warned against | Budget for certificates early; unsigned builds are a support burden from day one |
| Restore is never actually exercised | Recovery fails when it matters | §8 drill is a release gate, re-run every release |
| Scope | The programme stalls | Phases 0–3 deliver standalone value even if 4–6 slip |

---

# 8. Acceptance Tests

The programme is complete when all three pass, on evidence rather than
assertion.

## 8.1 Clean install and uninstall

On Windows, macOS and Linux: install from the produced installer on a machine
with no Python and no database; complete the first-run wizard; record an
animal and a milk entry; uninstall; confirm the application is gone and that
farm data was retained or removed according to the choice made at uninstall.

## 8.2 Mobile

From an Android phone and an iOS phone on the farm LAN: install the PWA to the
home screen; view herd and milk status; record a milk yield; receive a
finding. Then disable the network, record two entries offline, re-enable, and
confirm the sync-results screen reports each entry's outcome accurately —
including a deliberately out-of-sequence entry, which must be reported as
needing attention rather than silently accepted or silently dropped.

## 8.3 Simulated total failure

1. Populate a farm with representative data across every module.
2. Take a backup; confirm it verifies.
3. **Destroy the database** — delete the file and the storage directory.
4. Restore from backup through the UI.
5. Confirm every module's data matches the pre-failure state, including
   milking session ledger rows, `session_ledger` flags and NULL-versus-zero
   yields, which are precisely the distinctions a careless backup would flatten.

---

# 9. Open Items

- **Code signing certificates** — required for Windows and macOS distribution;
  a procurement decision, not a technical one.
- **Update distribution** — the Tauri updater needs a hosted manifest. Where
  it is hosted is undecided.
- **Cloud backup provider** — the interface is in scope for the first release;
  the implementation and provider are not.
- **Multi-farm deployments** — out of scope here. PostgreSQL support is
  retained so this remains open rather than foreclosed.

---

*End of IM-013.*
