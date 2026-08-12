# DairyOS Implementation Plan — Chapters 6–10

## 1. Programme objective

Implement the approved operational modules without creating parallel sources of truth. The governing rules are:

- `GET /farm/reference-data` is authoritative for enums/vocabularies.
- One persisted source of truth per business fact.
- Shared classifiers/reducers replace endpoint-local vocabularies.
- Existing unwired domain scaffolding is adapted before new models are designed.
- Event-journal endpoints are treated as audit inputs, not queryable domain state, until projected into persisted models.
- `OperationalInputProjectionBridge` and every `*IntelligenceService` must be tested end-to-end; a bridge that accepts a payload but stores the wrong shape is considered broken.
- Exact `method + path` collisions are regression-tested.
- Frontend degraded/quality states come from the backend; no synthetic values.

## 2. Global dependency order

1. **Baseline guardrails:** route inventory/collision tests, reference-data contract tests, projection-bridge tests, migration smoke tests.
2. **G3.1:** canonical milk-session schema; prerequisite for A4/drop alerts, Record Milk and yield comparisons.
3. **G7.1 / Tier 1d:** real worker identity + farm-scoped RBAC; prerequisite for Workforce.
4. **G8.3 / feed-item price catalog:** canonical inventory item master; prerequisite for Chapter 4 cost analytics.
5. Chapter 6 — Breeding.
6. Chapter 7 — Workforce.
7. Chapter 8 — Inventory.
8. Chapter 9 — Equipment.
9. Chapter 10 — Finance.
10. Cross-module hardening, migrations, regression/E2E tests, dead-code cleanup.

---

# 3. Chapter 6 — Breeding

### G6.1 — Canonical event vocabulary (P0)

Canonical values are `HEAT_OBSERVED`, `AI`, `PREGNANCY_CONFIRMED`, `PREGNANCY_NEGATIVE`, `DRY_OFF`, `CALVING`.

Implementation:
- Make `BreedingEntryRequest.event_type` a fixed enum.
- Create one shared classifier/state reducer used by `reproduction_management.py`, `farm_planning.py`, `farm_intelligence.py`, and the Animal Profile reproduction tile.
- Define current-state precedence from the latest valid event; `CALVING` closes/resets the pregnancy cycle.
- Run a one-time migration of existing `breeding_records` from legacy spellings to canonical values.
- Reject non-canonical writes after cutover.
- Add classifier matrix and historical-alias tests.

### G6.3 — Due/Overdue aggregate

Add `GET /farm/reproduction/due-to-calve`. Reuse the existing per-animal `last_insemination + 283 days` calculation. Return animal, due date, overdue flag and days until/past due. A recorded `CALVING` removes the animal from due/overdue cohorts.

### G6.4 — Breeding calendar

Add `GET /farm/reproduction/calendar?month=YYYY-MM`. Include derived due dates, scheduled pregnancy checks where such scheduling data exists, and predicted heat only when derivable from available history. Clearly distinguish predictions from observed facts.

### G6.6 — Breeding IDs

Migrate event IDs to `BR-YYMMDD-NNN`. Preserve legacy UUID references during migration if external references exist; make allocation concurrency-safe.

### G6.2/G6.5

Resolve the `/farm/kpis` exact-route collision. After tests cover the live implementation, retire/deprecate the five inert breeding/pregnancy files so they cannot be mistaken for the live model.

**Exit:** identical reproductive stage classification everywhere; stage counts reconcile with history; due/overdue lists reconcile with per-animal results; conception-rate semantics remain unchanged.

---

# 4. Chapter 7 — Workforce

### G7.1 — Worker identity/RBAC (P0)

Replace the shared environment-derived admin identity with farm-scoped authenticated users. Minimum authorization roles: Owner, Manager, Milker. Keep authentication/authorization roles distinct from the governed operational `workforce_roles` vocabulary (`VETERINARIAN`, `HERDSMAN`, `MILKER`, `FEEDER`, `MANAGER`, `ADMIN`). Persist user/farm membership and migrate the shared-admin setup. New operational writes must be attributable to an identity.

### G7.2 — Workforce persistence

Persist worker activity with identity, operational role, timestamp, activity type/value and optional task/shift linkage. Keep the existing endpoint shape compatible where possible; eliminate free-text worker identity once roster exists.

### G7.3 — WorkSchedule/WorkShift

Adapt the existing dataclass shapes rather than redesigning them. Add database persistence, repository and API. Link shifts/tasks to real workers; support To Do/In Progress/Completed and preserve completion percentage semantics.

### G7.4 — OperationalShift

Persist the existing shift-handoff model: supervisor, status, start/end and transferred actions. Link it to real worker identities and derive attendance/on-duty from persisted assignments.

### G7.5 — Performance/activity

Build last, from persisted facts: tasks completed, completion rate, activity volume and shift attendance. Avoid speculative employee scoring.

**Exit:** roster/identity survives restart; staff/on-duty KPIs are reproducible; tasks and shifts persist; every activity is attributable.

---

# 5. Chapter 8 — Inventory

### G8.1 — Canonical ledger architecture (P0)

Use a single `InventoryItem` catalog plus a transaction ledger. Every movement is `RECEIVE` or `ISSUE`, matching the live endpoint's existing direction. Current stock is derived from movements, never stored as a second mutable balance. Coverage/status is computed on read from ledger + consumption history.

Adapt/retire the two snapshot-style feed/medicine designs after parity tests. Investigate `operations/intelligence/models/feed_inventory.py` before removal/deprecation.

### G8.2 — Bridge integration

The `inventory_status_recorded` projection must reference canonical inventory facts where intelligence requires them; a generic status dict must not be treated as stock quantity.

### G8.3 — Feed price catalog

Implement `InventoryItem` with `INV-YYMMDD-NNN`, name, category (`FEED`/`MEDICINE`/`SUPPLIES`/`OTHER`), unit, current `cost_per_unit`, reorder threshold and nullable `drug_reference` link. Feed records/rations reference `item_id` and snapshot cost at entry time so historical costs survive later price changes.

### G8.4 — Medicine

Medicine inventory uses the same catalog/ledger and links to `drug_reference`. `drug_reference` remains safety/withdrawal authority and is not merged with stock data.

**Exit:** purchase/consumption history is auditable; balance survives restart and is derivable from movements; feed and medicine use one architecture; G4.1 cost linkage works historically.

---

# 6. Chapter 9 — Equipment

### G9.1 — Governed status fix

Keep `AVAILABLE`, `IN_USE`, `MAINTENANCE`, `OUT_OF_SERVICE`. Rewrite equipment intelligence to act on `OUT_OF_SERVICE` and, once due dates exist, overdue maintenance; remove unreachable `ATTENTION`/`FAILED`/`CRITICAL` checks. Preserve the daily visibility/freshness check.

### G9.2 — Equipment entity

Persist `EQ-YYMMDD-NNN`, name, category, status, location, `last_service_at`, `next_service_due_at`, and `running_hours_total`.

### G9.3 — Maintenance

Add service records and one manually-set `next_service_due_at`. No recurring scheduling engine. A service updates last-service date and may set the next due date.

### G9.4 — Repairs

Add repair records with date, cause, status, downtime start/end, cost and notes. Keep repair separate from routine maintenance.

### G9.5 — Runtime

Persist usage deltas/events and derive running total. Add idempotency protection against duplicate submissions.

**Exit:** governed status can trigger intelligence; runtime accumulates; service due state is reproducible; maintenance and repair history/costs are queryable.

---

# 7. Chapter 10 — Finance

### G10.1 — Payment method

Add governed `payment_method` to `FinancialTransaction` (`CASH`, `BANK`, `TRANSFER`, `CARD`, `OTHER`) and actually persist it from the entry request. Do not create a full Account entity. Cash in Hand and Money at Bank are derived from tagged transactions. Historical rows without a known method remain unknown rather than being reconstructed.

### G10.2/G10.3 — Category correctness

Keep `GET /farm/reference-data` as source of truth. Fix `CostOfProductionService` hardcoded sets to match `MILK_SALES` and `OTHER_OPERATING` verbatim. Add tests covering every governed financial category and milk-revenue detection.

### G10.4 — Financial intelligence

Remove dependence on payload fields the live API cannot produce (`awareness_status`, `cash_available`, `minimum_cash_required`). Replace with a persisted-transaction-derived negative cash-flow/expense-over-income check using the same source as reconciliation. Keep visibility check. Ensure signals are deterministic and non-duplicative.

### G10.5 — Reconciliation

Extend periods to Today, This Week, Monthly, Quarterly, Yearly. Add manual actual-balance entries per payment-method bucket; compare actual vs system-computed total with a centrally defined tolerance. Green ≈ zero variance; amber = nonzero variance with an entry; red = no current-period manual entry. No bank-feed integration in this scope.

### G10.6 — Scope boundary

No budget, depreciation, accrual accounting or asset valuation in this release. Finance remains a cash-basis income/expense ledger.

**Exit:** payment method survives write/read; milk revenue and OTHER_OPERATING classify correctly; cost-of-production quality is honest; reconciliation is reproducible; financial intelligence is triggerable from persisted data.

---

# 8. Cross-module integration

- IDs: preserve existing animal convention; breeding `BR-YYMMDD-NNN`; inventory `INV-YYMMDD-NNN`; equipment `EQ-YYMMDD-NNN`; worker IDs stable and distinct from display names.
- Animal Profile and all reproduction surfaces consume the same breeding classifier.
- Feed cost flow: `InventoryItem.cost_per_unit` → feed-entry cost snapshot → production/cost analytics → Finance.
- Medicine flow: treatment → `drug_reference` for safety + inventory item for stock/cost.
- Workforce identity should be available for breeding, inventory, equipment and finance audit attribution where applicable.
- Command Center intelligence must consume persisted facts or validated projections; every alert condition must be triggerable by a valid operator/API input.

# 9. Migration protocol

1. Add new nullable tables/columns.
2. Backfill canonical values.
3. Validate row counts/referential integrity.
4. Switch reads to canonical models/classifiers.
5. Switch writes to governed validation/persistence.
6. Remove/deprecate legacy paths only after parity tests.
7. Record migrated, unresolved and rejected row counts.

Breeding aliases are migration-only. Finance historical payment method remains unknown where not recorded.

# 10. Testing programme

### Unit
Classifier matrices; financial category mappings; inventory balances/coverage; due/overdue dates; runtime accumulation; reconciliation tolerance.

### API contracts
Reference-data validation; new endpoint schemas; filters/pagination; idempotency.

### Integration
Write→persist→read parity; bridge→intelligence triggerability; cross-module references.

### Regression
Exact route collision detection; existing KPI/reproduction/cost endpoints; migrated legacy records.

### E2E acceptance journeys
- Breeding: Heat → AI → Pregnancy Check → Pregnant → Due → Calved.
- Workforce: user → role → shift → task → completion.
- Inventory: item → purchase → consumption → balance → reorder.
- Equipment: asset → usage → maintenance → repair → cost/history.
- Finance: transaction → payment method → reconciliation → cost of production → intelligence.

# 11. Delivery waves

| Wave | Scope | Exit |
|---|---|---|
| 0 | Guardrails | Routes/reference/bridge/migration tests pass |
| 1 | G3.1 milk session | Milk fact canonical |
| 2 | G7.1 RBAC/identity | Real worker identity exists |
| 3 | G8.3 item/price catalog | Feed cost link exists |
| 4 | Chapter 6 | Unified reproductive state |
| 5 | Chapter 7 | Persisted roster/task/shift system |
| 6 | Chapter 8 | Catalog + movement ledger + medicine stock |
| 7 | Chapter 9 | Asset + maintenance + repair + usage |
| 8 | Chapter 10 | Payment tagging + cost correctness + reconciliation |
| 9 | Integration hardening | E2E/migration parity |
| 10 | Cleanup | Dead code/deprecated paths removed |

## Programme definition of done

No duplicate authoritative model; no governed-vocabulary contradictions; no intelligence rule depends on impossible payload fields; every new persisted model has migration/repository-service/API/tests; every migration has reconciliation checks; every KPI has a declared source and degraded-state behavior; existing live endpoints remain compatible unless a binding decision explicitly requires change.
