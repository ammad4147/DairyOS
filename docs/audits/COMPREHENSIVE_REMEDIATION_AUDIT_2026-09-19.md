# DairyOS Comprehensive Remediation and Independent Forensic Audit

Status: IN PROGRESS — no final clearance issued

## Starting repository gate

- Repository: `D:\DairyOS`
- Branch: `main`
- Starting `HEAD`: `15e742364719825ce6f0c5dd800751e3bcfc8b07`
- Fetched `origin/main`: `15e742364719825ce6f0c5dd800751e3bcfc8b07`
- Relationship: ahead 0, behind 0
- Worktrees: primary `D:\DairyOS` only
- Starting staged changes: none
- Starting unstaged changes: none
- Starting untracked files: none
- `git diff --check`: passed

## Stage 1 — OperationalState concurrency authority

### Completed

- Enumerated current writers to `OperationalStateModel`.
- Traced the shared `state_payload` read-modify-write pattern.
- Ran the existing focused heat-stress, farm-intelligence, and welfare tests in
  a disposable local PostgreSQL cluster.

### Evidence

- `src/dairyos/api/farm_planning.py`: `ration_plans` writer.
- `src/dairyos/api/animal_welfare.py`: `animal_welfare_observations` writer.
- `src/dairyos/api/farm_intelligence.py`: `heat_stress_observations` and
  `sop_protocols` writers.
- `src/dairyos/api/heat_stress_intelligence.py`:
  `heat_stress_observations` writer.
- `src/dairyos/data/repositories/database_operational_state_repository.py`:
  canonical `FarmOperationalState` field writer.
- Baseline focused tests: 11 passed in 1.11 seconds against an isolated
  `dairyos_test` PostgreSQL database.

### Findings

#### OSTATE-001 — CONFIRMED DATA-INTEGRITY RISK — MAJOR

Each writer independently loaded the same per-farm JSON payload, modified a
copy, and replaced the whole payload without serialization. Two sessions can
therefore overwrite each other's same-key or different-key changes. Concurrent
first-row creation can also race on the unique `farm_id` constraint. Existing
focused tests were single-request tests and did not exercise this behavior.

### Changes

- Added one transaction-scoped operational-state mutation boundary using a
  per-farm PostgreSQL advisory lock plus an existing-row `FOR UPDATE` lock.
- Migrated all active JSON-envelope writers to that boundary: canonical farm
  state, ration plans, welfare observations, SOPs, and both heat-stress routes.
- Changed the welfare mutation endpoint from a process-shared SQLAlchemy
  session to an operation-owned session.
- Retained the farm operational-date authority when mutations update the
  projection row.

### Tests

- Pre-change focused API baseline: PASS, 11 passed.
- Post-change focused API, persistence, projection, independent-session
  concurrency, first-row creation, same-key append, different-key mutation,
  and injected rollback tests: PASS, 20 passed in 1.78 seconds.
- Focused Ruff check: PASS with existing unrelated rules explicitly excluded
  (`B008`, `UP017`, `FURB162`, and `RUF012`).
- Python compilation: PASS.
- `git diff --check`: PASS.

### Repository state

- Clean at the starting gate.
- Current remediation changes are intentionally uncommitted pending focused
  verification and forensic review.

### Remaining

- Continue the remaining domain, migration, security, package, and installed
  runtime audit stages.

### Next

Forensically classify `OperationalEventModel`, then enumerate ORM, schema,
migration, and runtime-bootstrap authority before disposable database
experiments.

## Stage 2 — Operational events and ORM registration

### Completed

- Traced `OperationalEventModel` imports, repository, runtime publisher,
  readers, Passport projection, tests, and its distinction from the durable
  event journal/outbox.
- Enumerated the runtime SQLAlchemy registry from a fresh Python process.
- Enumerated the Alembic graph and current head.
- Compared ORM-owned tables with migration-created tables.

### Evidence

- Runtime ORM catalog: 38 mapped classes and 38 tables.
- Alembic head: `20260915_01`.
- Event/publication/Passport focused tests: PASS, 12 passed in 0.17 seconds.
- `EventJournalModel` stores original event identity and payload for replay.
- `OperationalEventModel` stores a flattened application-query projection and
  is written through `OperationalEventPublisher` / `OperationalEventRepository`.
- Current readers include animal Passport history and milk operational trace.

### Findings

#### OEVENT-001 — INTENTIONAL DESIGN — VERIFIED

`OperationalEventModel` is an active query projection and compatibility-facing
operational trace. It is not the canonical replay journal. Creating a second
writer or deleting the table would be incorrect.

#### SCHEMA-001 — CONFIRMED TEST/CERTIFICATION GAP — MODERATE

Registration tests named only a few historically missing models and could pass
while another active model silently disappeared from fresh `create_all`
bootstrap. A complete 38-table model-registration contract has been added.

#### SCHEMA-002 — LEGACY/COMPATIBILITY — VERIFIED

Alembic contains migration-only `ai_assistant_conversations`,
`ai_assistant_messages`, and `cmp_scenarios`. Source search found no current
runtime reader or writer. The first two belong to the retired in-process
Assistant architecture; current `/assistant` uses the isolated knowledge
bridge. Supported upgrade retains/creates its historical tables, while fresh
runtime bootstrap correctly creates only the 38 active model-owned tables.
These legacy tables must not be promoted to new authorities merely for schema
symmetry; removal from upgraded farms requires a separate retention decision.

#### SCHEMA-003 — INTENTIONAL DESIGN — VERIFIED

Pure Alembic upgrade from a completely empty database is not a supported
bootstrap authority: the historical chain assumes the pre-Alembic ORM-created
baseline and fails when it reaches an `ALTER TABLE animal` operation. The
packaged fresh-install authority is explicitly `Base.metadata.create_all`,
destructive-guard installation, then an Alembic head stamp after private-
cluster provenance checks. Alembic owns supported upgrades from an established
stamped schema. The new experiment preserves this distinction rather than
silently treating the paths as interchangeable.

### Changes

- Added a complete ORM registration contract covering every active mapped
  table and mapper.

### Tests

- Complete registration and fresh development-bootstrap tests: PASS, 6 passed
  in 0.12 seconds.
- Disposable PostgreSQL schema experiments: PASS, 5 passed in 1.93 seconds.
  Fresh runtime bootstrap created all 38 active ORM tables and reached
  `20260915_01`; pure Alembic on empty was proven unsupported; a stamped
  `20260909_02` create-all baseline upgraded to the current head while
  retaining every active ORM table; fresh bootstrap and supported upgrade now
  match for active-table columns, data types, defaults, nullability, primary
  keys, foreign keys, unique constraints, indexes, and check constraints.

### Repository state

- Remediation remains uncommitted pending broader regression and forensic
  review.

### Remaining

- Determine whether migration-only legacy tables should remain upgrade-only or
  receive an explicit retirement policy.

### Next

Run the complete registration contract and disposable schema experiments.

## Stage 3 — Full regression classification

### Completed

- Ran the complete isolated local regression after the operational-state and
  schema-contract changes.
- Reproduced the only failure in isolation and traced its order dependency.

### Evidence

- Initial full isolated run: 3484 passed, 7 skipped, 1 failed in 141.14
  seconds.
- Failing test:
  `test_supervisor_logging_is_durable_but_not_startup_critical`.
- Isolated rerun of that test: PASS, 1 passed in 0.18 seconds.
- The failure occurs after a real Alembic command loads
  `db_migrations/env.py`; Python logging `fileConfig` defaults to disabling
  existing named loggers.

### Findings

#### WINLOG-001 — CONFIRMED DEFECT — MODERATE

The packaged supervisor configures its durable file logger before invoking the
migration gate. Alembic then disabled that existing logger, so later startup
diagnostics could be silently absent from `supervisor.log`. The full suite
exposed the same order-dependent behavior.

### Changes

- Configured Alembic logging with `disable_existing_loggers=False`.
- Added a direct migration-environment contract proving an existing DairyOS
  application logger remains enabled.

### Tests

- Focused logging and schema experiment rerun: PASS, 5 passed in 1.23 seconds.
- Full regression rerun after correction: PASS, 3486 passed and 7 skipped in
  141.84 seconds.
- Focused Ruff import ordering and lint check: PASS.
- Python compilation over migration, source, architecture tests, and
  remediation tests: PASS.
- `git diff --check`: PASS.

### Repository state

- Remediation remains intentionally uncommitted.

### Remaining

- Frontend, package, installed-runtime, and the remaining domain audit stages
  are not yet certified.

### Next

Continue the remaining domain, security, frontend, package, and installed-
runtime audit stages without issuing final clearance.

## Stage 4 — Frontend source verification

### Completed

- Verified the existing web application without making layout or capability
  changes.

### Evidence

- `npm run typecheck` from `src/DairyOS.Web`: PASS.
- `npm run build` from `src/DairyOS.Web`: PASS; Vite reported its existing
  large-chunk advisory warning.
- `git status --short -- src/DairyOS.Web`: no tracked or untracked web changes.

### Findings

- No frontend blockade or breakage was found in this pass.

### Remaining

- Installed packaged runtime acceptance remains pending.

## Stage 5 — Security and runtime-source contracts

### Completed

- Rechecked authentication, desktop-session, private database credential,
  private PostgreSQL environment isolation, supervisor startup, and startup
  integrity contracts through the isolated local test runner.

### Evidence

- Direct `pytest` invocation refused to run because the ambient database name
  was `dairyos`, confirming the destructive-fixture guard stayed active.
- Isolated runner focused security/runtime group: PASS, 84 passed in 3.01
  seconds against disposable `dairyos_test`.

### Findings

- No security or runtime-source blockade was found in this pass.
- Installed-runtime acceptance is still pending; source tests do not certify a
  packaged installation.

## Stage 6 — Packaging and install-source contracts

### Completed

- Rechecked the non-installing package, desktop build, installer presentation,
  installer data-choice, backup-task, preflight, installation-state,
  installation-choice, desktop-runtime, admin-complete, uninstall-preservation,
  and installation-fitness ORM contracts through the isolated local test
  runner.

### Evidence

- Isolated runner focused package/install-source group: PASS, 84 passed in
  8.69 seconds against disposable `dairyos_test`.

### Findings

- No package/source install-contract blockade was found in this pass.
- This is not an exact-SHA installer build, machine install, or installed
  runtime acceptance.

## Stage 7 — Operational date, Health withdrawal, and breeding lifecycle

### Completed

- Searched source routes and services for business-date defaults derived from
  `datetime.now()`, `date.today()`, UTC `.date()`, host-local time, and
  equivalent constructs.
- Separated technical timestamps, token/log/audit timestamps, and treatment
  clearance instants from farm business-date authority.
- Rechecked active Health withdrawal summary and withdrawal milk wastage paths.
- Recertified the existing event-oriented breeding lifecycle without creating
  duplicate PD, calving, pregnancy-loss, or calf endpoints.

### Evidence

- Milk production summary resolves its period anchor from the farm operational
  date before calculating default periods.
- Health summary counts withdrawal animals and follow-ups against
  `OperationalDateAuthority`.
- Withdrawal clearance remains an instant-based UTC safety calculation, while
  milk production/wastage uses the operator production date.
- Focused payroll/OPEX regression: PASS, 21 passed in 0.42 seconds.
- Focused heat-stress and operational-date regression: PASS, 16 passed in 0.76
  seconds.
- Focused breeding lifecycle recertification: PASS, 36 passed in 1.87 seconds.

### Findings

#### ODATE-001 — CONFIRMED DEFECT — MODERATE

Payroll payment settlement defaulted omitted `payment_date` to host-local
today. That could assign the paired Finance/OPEX transaction to the wrong farm
business day when the configured DairyOS operational date differed from the
Windows host date.

#### ODATE-002 — CONFIRMED DEFECT — MODERATE

Heat-stress intelligence anchored its read window to the UTC host date rather
than the farm operational date. Around farm-local day boundaries, recent
observations could be incorrectly included or excluded from the operational
heat-stress view.

#### BREED-001 — INTENTIONAL DESIGN — VERIFIED

The existing breeding lifecycle is event-oriented: insemination, pregnancy
diagnosis, pregnancy loss, calving, calf creation, semen movement, dashboard,
Animal Passport, and post-calving return derive from persisted breeding events
and propagation records. No missing runtime capability was established that
would justify duplicate PD/calving/loss/calf endpoints.

### Changes

- Changed payroll payment default dates to use `OperationalDateAuthority`
  through the active repository factory.
- Changed heat-stress intelligence read-window anchoring to use
  `OperationalDateAuthority`.
- Added regression coverage for both corrected business-date boundaries.

### Remaining

- Continue full domain authority tracing for Animals, Milk, Feed/TMR/COP,
  Finance/OPEX, Health/Vaccination, Dashboard, COML, Analytics, Reporting,
  Settings, Simulator, and Assistant.
