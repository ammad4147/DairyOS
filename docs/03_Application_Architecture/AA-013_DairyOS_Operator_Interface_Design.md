# AA-013 — DairyOS Operator Interface Design

**Document ID:** AA-013
**Version:** 1.3
**Status:** Approved Baseline
**Supersedes:** none
**Related:** AA-012 (Executive Command Center), AA-008 (Milk Production), AA-004 (Herd Management)

---

# 0. Revision History

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-08-13 | Initial baseline |
| 1.1 | 2026-08-13 | **Feed decoupled from the individual animal (D-UI-9, D-UI-10).** Animal Profile Feed tab removed; Feed Management rewritten around group-level batches; TMR Preparation specified as a subsection from the recovered `TMRLifeCycleManager`; the v1.0 recommendation to recover a per-animal feed array is **withdrawn as incorrect** |
| 1.3 | 2026-08-13 | **Cost of Production respecified as an independent manual calculator and moved to AA-014.** §15 replaced by a pointer; the integrated bottom-up cost chain, the latest-purchase-price valuation (D-UI-12) and the reconciliation finding (D-UI-13) are **withdrawn** — all four of their dependencies are unbuilt. D-UI-14 stands: it remains its own top-level section |
| 1.2 | 2026-08-13 | **Notification bell removed (D-UI-11)** — findings surface in their own sections, the action queue, and nav count badges. **Cost of Production added as a twelfth top-level section (D-UI-14)**, with feed valued at latest purchase price (D-UI-12) and bottom-up/top-down reconciliation raising a finding (D-UI-13). Sections renumbered from Records onward |

---

# 1. Purpose

Defines the DairyOS operator interface: the main dashboard and the eleven
sections beneath it.

This document is the reference for all frontend work. It specifies what each
screen answers, what it shows, what backend exists to serve it today, and what
backend must be built where it does not. Where a section cannot yet be built,
the missing work is named here rather than discovered later.

---

# 2. Governing Principles

These apply to every screen in the system. They are not stylistic; each one
exists because violating it produces a screen that misleads the operator.

## 2.1 Absence of data must never render as good news

A farm that stopped recording must never look identical to a farm with nothing
wrong. Every indicator that can be green must distinguish three states:

| State | Meaning | Presentation |
|---|---|---|
| Good | Evidence exists, and it is good | Green, with the evidence stated |
| Bad | Evidence exists, and it is bad | Amber or red |
| Unknown | No evidence was recorded | Neutral grey, explicitly labelled |

Concretely: Health shows `No open cases · 42 animals observed today`, not a
bare green tick. Herd composition shows an `Unclassified` count rather than
silently dropping animals with no lifecycle status. Milk totals state which
sessions they include.

This is the interface-layer expression of the G1.6 data model, where `NULL`
(not entered) and `0.0` (entered as zero) are deliberately distinct.

## 2.2 Every number states what it is comparing

No percentage appears without its basis visible. A drop of 23% is meaningless
until the reader knows it is this morning against yesterday morning.

## 2.3 Data that was never entered is excluded, not zeroed

All aggregates, averages and comparisons exclude:

- Sessions declared `NOT_MILKED`
- Yields that are `NULL`
- Rows with `session_ledger = false` (pre-ledger history, where a stored `0.0`
  is ambiguous and cannot be interpreted)

## 2.4 One finding, one identity, one lifecycle

A production drop is one thing. It must not exist as an alert, a notification
and a decision with three identities and three meanings of "resolved". See §4.

## 2.5 Clicking a thing opens that thing

Selecting an animal opens the Animal Profile — a screen with its own tabs and
its own history. It does not open a modal of loosely related fields.

---

# 3. Decisions of Record

Taken 2026-08-13. Recorded here so later work does not silently reverse them.

| # | Decision | Rationale |
|---|---|---|
| D-UI-1 | The main dashboard leads with a prioritised **action queue**, with the four domain panels beneath it | The dashboard's job is "what do I do now", not only "what is happening" |
| D-UI-2 | Per-animal drop detection is **same-session** comparison, surfaced in the Milk Production section | Day-total comparison fires on every animal every morning and would discredit the feature within a week |
| D-UI-3 | Drop severity: **red above 20%, amber 10–20%, none below 10%** | Confirmed against the previously agreed thresholds |
| D-UI-4 | The dashboard's headline comparison is **session-to-session until the day is complete, then day-to-day** | Preserves a true day-to-day figure without a misleading percentage during working hours |
| D-UI-5 | Alerts, notifications and command-centre decisions are **one entity with one ID allocator** | Prevents three identities and three definitions of "resolved" for one event |
| D-UI-6 | `CLOSE_UP` is a **lifecycle stage in its own right** | It is how Herd Dynamics counts animals, and the registration endpoint already accepts it |
| D-UI-7 | First build target is **the main dashboard itself** | Fastest route to seeing the system whole; panels degrade gracefully where sections are thin |
| D-UI-8 | This document covers **all eleven sections plus the backend work each blocked section requires** | Blocked work stays visible rather than forgotten |
| D-UI-9 | **Feed is never linked to an individual animal.** Feed is recorded against a group or pen only, and `animal_id` is removed from the feed record entirely | TMR is prepared in batches for a group. A per-animal feed record is not something a farm can actually produce, so recording one invents data |
| D-UI-10 | The Animal Profile has **no Feed tab** | Follows from D-UI-9. Feeding is a group concern and belongs in the Feed Management section |
| D-UI-11 | **No notification bell.** Findings surface in their owning section, in the dashboard action queue, and as count badges on section navigation | The action queue already guarantees nothing goes unseen; a bell would be a second inbox for the same items |
| ~~D-UI-12~~ | ~~Feed items valued at latest purchase price~~ — **withdrawn v1.3**, superseded by AA-014 (manual entry, D-COP-5) | Retained in the record because the staleness-guard reasoning still applies if valuation is ever automated |
| ~~D-UI-13~~ | ~~Bottom-up/top-down reconciliation raises a finding~~ — **withdrawn v1.3**, superseded by AA-014 (D-COP-1, independence) | The reasoning stands for a future integrated design; it is not buildable on the current backend |
| D-UI-14 | **Cost of Production is its own top-level section**, not a subsection of Finance or Milk | It draws on feed, labour, health, breeding and equipment together, and is central enough to the business to have its own home |

---

# 4. The Operational Finding

The single cross-cutting entity behind the action queue, every section's alert
list, and the navigation count badges.

## 4.1 Why one entity

Every module produces findings that need a human: a production drop, a
high-severity health observation, medicine below reorder level, equipment
maintenance due, a heat detected. These share a lifecycle and differ only in
origin. Modelling them separately means writing that lifecycle five times and
reconciling five notions of "resolved".

The backend already has the lifecycle:
`POST /command-center/decisions/{id}/acknowledge` and `/resolve` are live. The
finding entity extends that rather than replacing it.

## 4.2 Identity

Format: `<PREFIX>-YYMMDD-NNN`, allocated by one shared sequence per module per
day — the same scheme as the `MS-YYMMDD-NNN` milking session records shipped in
G3.1.

| Prefix | Source module |
|---|---|
| `AL` | Milk production |
| `HL` | Health |
| `BR` | Reproduction |
| `INV` | Inventory |
| `EQ` | Equipment |
| `FD` | Feed |
| `WF` | Workforce |
| `FN` | Finance |

## 4.3 Shape

| Field | Notes |
|---|---|
| `finding_id` | `AL-260813-001` |
| `raised_at` | Timestamp |
| `source_module` | Governed vocabulary |
| `subject_type` / `subject_id` | e.g. `ANIMAL` / `AN-…`, so the finding routes to a record |
| `severity` | `CRITICAL` / `HIGH` / `MONITORING` / `INFORMATION` |
| `title` | One line, operator language |
| `detail` | The evidence — the numbers behind the claim |
| `status` | `RAISED` → `ACKNOWLEDGED` → `RESOLVED` |
| `resolved_at`, `resolved_by`, `resolution_note` | |
| `route` | Where clicking it goes |

## 4.4 Lifecycle rules

- A finding is removed from the bell only when **resolved**, never on view.
- Acknowledging records that a human has seen it; it stays in the queue.
- Re-detection of an already-open finding updates it rather than raising a
  duplicate. One cow dropping for four consecutive days is one finding with
  four observations, not four alerts.
- Resolution requires a note when severity is `CRITICAL`.

## 4.5 Where findings surface

Per D-UI-11 there is **no notification bell**. A bell and the action queue would
both list unresolved findings, which is two inboxes for one set of items.

Findings appear in exactly three places, each answering a different question:

| Surface | Question it answers |
|---|---|
| **Owning section** | "What is wrong in this part of the farm?" |
| **Dashboard action queue** | "What needs a human today, across everything?" |
| **Nav count badge** | "Is something waiting somewhere I am not looking?" |

The nav badge carries the unresolved count on each section's navigation item —
`Health (2)`, `Inventory (1)` — so a finding raised while an operator is deep
in another section is still visible from anywhere, without a separate inbox to
manage. Critical counts are visually distinct from lower severities.

A badge clears only when its findings are **resolved**, never on view.

**Backend status:** the decision lifecycle exists; the finding entity, the ID
allocator, the detection engines and a per-section unresolved-count endpoint do
not. See §18.1.

---

# 5. Main Dashboard

## 5.1 Action Queue

The top of the screen. Between three and five findings that need a human today,
ranked by severity then age, drawn from every module.

Each row: severity marker, finding ID, one-line statement, and the action that
resolves it. Clicking routes to the underlying record.

If nothing needs attention, the queue says so explicitly and states what it
checked — per §2.1, an empty queue must not be indistinguishable from a queue
that was never populated.

## 5.2 The four panels

Beneath the queue. Each panel offers display options within itself; defaults
are fixed and specified below.

### Panel 1 — Milk Production

Always visible:

- **Today's Production**, labelled with what it includes — `210 L · morning
  recorded · evening outstanding`. Reads from `GET /farm/milk/next-session`.
- **Milk Sold**

Headline comparison, per D-UI-4:

- While the day is incomplete: session-to-session — `Morning 210 L vs 224 L
  yesterday morning, −6%`
- Once every observed session is settled: day-to-day — `Today 512 L vs 534 L
  yesterday, −4%`

Also present: count of open production findings, routing into the Milk section.

The period selector (7 days / 30 days / 3 months / 6 months / year / custom)
and the trend graph live in the **Milk Production section**, not on the
dashboard panel. The panel answers "is today normal"; the section answers "what
has been happening".

### Panel 2 — Herd Dynamics

Total · Milking · Dry · Close-up · Heifers · Calves · Unclassified.

Default presentation tabular; pie chart available. Clicking any segment opens
Herd Dynamics filtered to that group.

### Panel 3 — Health & Vaccinations

Green only when observations exist and no cases are open, stated as
`No open cases · N animals observed today`. Otherwise the list of animals
requiring attention, each ID routing to the Animal Profile health tab.

Distinct grey state when no observations have been recorded.

### Panel 4 — Reproductive Health

Due for Heat · Inseminated · Pregnant · Repeaters · Miscarriages. Each count
clickable into the Reproduction section, filtered.

---

# 6. Section 1 — Herd Dynamics

**Question: what animals do we have, and what is happening with each one?**

**Backend readiness: BUILDABLE NOW.**

## 6.1 Header

`Animals — 7 Total · 4 Milking · 1 Dry · 1 Heifer · 1 Calf`

Actions: Add Animal · Import · Export.

## 6.2 Registry

Search and filters across: Animal ID, name, status, lifecycle, sex, breed,
location/pen, health status.

| ID | Animal | Type | Status | Milk Today | Health | Reproduction |
|---|---|---|---|---|---|---|
| 1258 | Cow 1258 | Cow | Milking | 10.4 L | ⚠ Attention | Pregnant |
| 1023 | Cow 1023 | Cow | Milking | 12.6 L | Good | Heat detected |

`Milk Today` follows §2.1: blank-with-marker where no session has been entered,
never `0.0`.

## 6.3 Animal Profile

Tabs: **Overview · Milk · Health · Breeding · Treatments · History**.

There is deliberately **no Feed tab** (D-UI-10). Feed is prepared in batches
for a group, so no truthful per-animal feeding record exists to display.

Built on the existing `LifetimeAnimalPassportService` and
`GET /farm/animals/{animal_id}/passport`, which currently assembles milk,
health, breeding, treatments, feed, finance and a merged timeline. **The feed
projection is removed** — see §7A.5.

## 6.4 Backend work required

- Add `CLOSE_UP` to the governed lifecycle vocabulary in
  `api/reference_data.py` (D-UI-6).
- **Reconcile the lifecycle vocabulary.** Three definitions currently disagree:
  `reference_data.py` advertises `SOLD`/`DECEASED`; `animal_registration.py`
  enforces `CLOSE_UP`/`SICK`/`CULLED`; the existing dropdown offers a third
  set. Settle one list, have registration import it rather than duplicate it,
  and drive the dropdown from `GET /farm/reference-data`.
- Retiring an animal (`SOLD`, `DECEASED`) currently returns 422 and has no
  working path. Required before the registry is honest.

---

# 7. Section 2 — Milk Production

**Question: how much milk are we producing, and where are we losing it?**

**Backend readiness: BUILDABLE NOW.** G3.1 and G1.6 shipped 2026-08-13.

## 7.1 Header and period selector

7 Days · 30 Days · 3 Months · 6 Months · Year · Custom.

## 7.2 KPI row

Total Production · Average/Day · Average/Cow · Morning · Evening · Open drop
findings.

Average/Cow excludes animal-days with no entered yield — `dairy_kpi.
_has_entered_yield()` already enforces this.

## 7.3 Main chart

Total production over the selected period, with previous-period comparison and
a Morning / Evening / Total selector.

## 7.4 Production by animal

| Animal | Today | Previous | Change | Status |
|---|---|---|---|---|
| Cow 1001 | 16.8 L | 11.6 L | +44% | Good |
| Cow 1258 | 10.4 L | 13.5 L | −23% | 🔴 Alert |

Sortable. `Previous` is the same session on the prior recorded day (D-UI-2).

## 7.5 Production Drop Findings

Per D-UI-2 and D-UI-3. Same-session comparison, per animal:

- **Red** — decline above 20%
- **Amber** — decline 10–20%
- **None** — below 10%

Excluded from detection per §2.3: `NOT_MILKED` sessions, `NULL` yields, and
`session_ledger = false` rows.

Presented as:

```
AL-260813-001
Cow #1258 — production dropped 23%
13.5 L → 10.4 L  (morning vs yesterday morning)
Review animal →
```

Routing: finding → Animal Profile → Milk tab, with the Health and Breeding
tabs one click away, because the explanation for a drop is usually in one of
them.

## 7.6 Session ledger surface

The Milk section exposes what G3.1 built and no screen yet shows:

- Which sessions are settled today, and which are outstanding
  (`GET /farm/milk/next-session`)
- The ability to declare a session not milked, with a governed reason
  (`POST /farm/milk/not-milked`)
- The out-of-sequence refusal (HTTP 409) rendered as operator guidance, showing
  both routes forward — record the outstanding session, or declare it not
  milked

## 7.7 Backend work required

- Drop detection engine, persisting findings per §4 (G3.4).
- Period aggregation endpoints for the trend chart.

---

# 8. Section 3 — Feed Management

**Question: what are we feeding, how much, and what is it costing?**

**Backend readiness: BUILDABLE NOW for events and rations; costing is partial.**

## 8.1 The unit of feeding is a group, never an animal

Per D-UI-9. TMR is mixed in a batch and delivered to a pen. There is no moment
at which a farm measures what one cow ate, so a per-animal feed record would be
a number nobody produced. Every screen, endpoint and table in this section is
keyed on **group or pen**.

The ration backend already reflects this correctly: `FeedRation` is keyed on
`animal_group`, not `animal_id`.

## 8.2 KPI row

Feed consumed today · this week · Feed cost · Cost/animal · Cost/litre ·
Inventory cover.

`Cost/animal` is a batch cost divided by the head count of the group — an
allocation, not a measurement, and labelled as such.

## 8.3 Subsections

1. **TMR Preparation** (§8.4)
2. **Feed Events** — batches recorded against a group or pen
3. **Feed Inventory**
4. **Rations** — the stored formulas
5. **Consumption Analysis**

## 8.4 TMR Preparation

The heart of this section, and the reason it exists.

Recovered from commit `9e23f01` (11 Aug 2026), where it was added as
`TMRLifeCycleManager.tsx` before being removed in error by `4e84113`
(*"chore(web): remove legacy component tree"*). Both files are preserved at
`docs/recovery_artifacts/web_prototypes/`.

### Ingredients

Eleven, each with unit, step, bounds and price (PKR):

| Ingredient | Unit | Step | Max | Price |
|---|---|---|---|---|
| Silage | kg | 0.5 | 60 | 20 |
| Vanda (Concentrate) | kg | 0.5 | 25 | 100 |
| Wheat Straw | kg | 0.5 | 12 | 20 |
| Soybean Meal | kg | 0.25 | 5 | 180 |
| Molasses | kg | 0.25 | 3 | 85 |
| Bypass Fat | g | 25 | 600 | 480 |
| Mineral Mixture | g | 25 | 400 | 460 |
| Meetha Soda | g | 25 | 400 | 200 |
| Anionic Salts (DCAD) | g | 25 | 300 | 350 |
| Toxin Binder | g | 10 | 150 | 260 |
| Lysine / Methionine | g | 5 | 80 | 4000 |

### Stage formulas

Seven lifecycle stages, each a per-head preset with a production target and
written guidance:

| Stage | Target |
|---|---|
| Early Lactation (0–70 DIM) | 30–35 L/day · high energy density · peak stress |
| Mid Lactation (70–200 DIM) | 20–25 L/day · rumen stability · monitor BCS |
| Late Lactation (200–305 DIM) | 10–15 L/day · avoid over-conditioning |
| Far-Off Dry (>21d pre-calving) | high fibre, low energy · prevent obesity |
| Close-Up (last 21d pre-calving) | transition diet · negative DCAD |
| Growing Heifer | 700–900 g/day gain · moderate protein |
| Calf Starter (4–8 weeks) | rumen development · fresh mix only |

The stage list independently confirms D-UI-6: Close-Up is a real stage in the
farm's own nutritional practice.

### Governed interlocks

The formulas carry nutritional rules that the UI must enforce, not merely
display. The known one: **anionic salts and Meetha Soda must not be combined**
— the close-up ration manages negative DCAD, and sodium bicarbonate defeats it.
Attempting the combination is refused with the reason, in the same style as the
milk sequencing refusal.

### Calculation

Per-head quantities × group head count → batch weight and batch cost. Both
per-head cost and batch cost are shown before the batch is committed, so the
operator sees the money before mixing rather than afterwards.

### Persistence

Formulas are stored **server-side**, in the existing `FeedRation` table,
extended where the stage presets need fields it lacks (step, min/max bounds,
per-ingredient price).

The recovered component persisted to `localStorage` under
`dairyos_tmr_lifecycle_v1`. That must not be carried forward: it confines a
farm's tuned formulas to one browser profile on one machine, keeps them
invisible to backup, and loses them to a cache clear. Formulas are farm data.

A second, parallel ration model is deliberately **not** created. DairyOS has
repeatedly been damaged by two representations of one concept — three breeding
classifiers, three lifecycle vocabularies. `FeedRation` is extended instead.

## 8.5 The connection that matters

Feed must resolve as a chain, not isolated tables:

```
Feed Batch → Group → Milk (of that group) → Cost per litre
```

Cost per litre is the number that justifies the module.

**Consequence of D-UI-9 worth planning for:** attributing a group's feed cost
to its milk requires knowing which animals were in which group *at the time*.
`Animal.production_group` is currently a plain string, so moving an animal
silently rewrites history. Group membership needs `effective_from` /
`effective_to` records — the pattern `AnimalMilkingScheduleHistory` already
uses for milking frequency. Required for costing; not required for the Animal
Profile, which per D-UI-10 shows no feeding at all.

## 8.6 Backend work required

- **Remove `animal_id` from feed** (D-UI-9): the `FeedRecord` column, the
  `FeedEntryRequest` field, and the feed projection in
  `LifetimeAnimalPassportService` (line 81, surfaced at line 94). Migration
  required for existing rows.
- Extend `FeedRation` for stage presets; expose CRUD so formulas are editable
  and versioned.
- Feed endpoints are spread across `api/feed_management.py` and
  `api/farm_planning.py` and need collapsing (G4.2).
- `Inventory cover` and `Feed cost` depend on the inventory ledger — see §12.
- Feeding-group membership history, for costing (§8.5).

# 9. Section 4 — Health Management

**Question: which animals need attention right now, and what happened to them?**

**Backend readiness: BUILDABLE NOW for observations; case management missing.**

## 9.1 KPI row

Active Cases · Critical · Under Treatment · Withdrawal Animals · Overdue
Follow-ups.

## 9.2 Animals requiring attention

Severity hierarchy: 🔴 Critical · 🟠 High · 🟡 Monitoring · 🟢 Resolved.

## 9.3 Health case timeline

```
Observation → Diagnosis → Treatment → Withdrawal → Follow-up → Resolution
```

The treatment record connects automatically to milk withdrawal. This interlock
already exists and is enforced on milk entry: an animal under active withdrawal
returns status `WITHHELD` with a safety message, and that status survives
subsequent sessions on the same day.

## 9.4 Backend work required

- **`HealthCase` entity (G5.1).** Observations exist; a case that spans
  observation through resolution does not. Without it, "Active Cases" and
  "Overdue Follow-ups" have nothing to count.

---

# 10. Section 5 — Reproductive Health

**Question: where is every animal in the reproductive cycle?**

**Backend readiness: BUILDABLE NOW for events; classification is unreliable.**

## 10.1 KPI row

In Heat · Inseminated · Pregnant · Due to Calve · Overdue · Conception Rate.

## 10.2 Reproduction pipeline

```
Heat → Inseminated → Pregnancy Check → Pregnant → Due → Calved
```

Then: Breeding Calendar, and Animal Reproductive History.

## 10.3 Backend work required — blocking

- **Unify the three breeding classifiers (G6.1).** The same animal currently
  reads `Pregnant` on one screen and `Unknown` on another, because three
  independent classifiers disagree. A pipeline visualisation built on
  contradictory classification will display contradictory counts. This must be
  fixed before the section is built, not after.
- Governed `BR-` identifiers for breeding records (G6.6).
- Five dead breeding files to remove (G6.5).

---

# 11. Section 6 — Workforce

**Question: who is working, what has been done, where do responsibilities sit?**

**Backend readiness: WRITE-ONLY. Cannot be built as specified.**

`POST /farm/workforce` accepts an entry into the operational event stream.
There is no table, no repository and no query path. Nothing can be read back.

## 11.1 Intended design

KPI row: Staff Present · On Duty · Tasks Today · Completed · Outstanding.

Areas: Today's Workforce (staff / role / shift / status / tasks); Task Board
(To Do → In Progress → Completed); Attendance and shifts; Activity.

Operational in emphasis, not HR.

## 11.2 Backend work required

- `Worker` entity with role and shift.
- `Task` entity with assignment, state and completion, raising findings for
  overdue items.
- Attendance records.
- Query endpoints for all three.

---

# 12. Section 7 — Inventory

**Question: what do we have, what is running low, what needs ordering?**

**Backend readiness: WRITE-ONLY. Cannot be built as specified.**

`POST /farm/inventory` writes to the event stream only. There is no balance,
so "Low Stock", "Out of Stock" and "Reorder" have nothing to compute from.

## 12.1 Intended design

KPI row: Total Items · Low Stock · Out of Stock · Expiring Soon · Inventory
Value.

| Item | Category | Stock | Unit | Reorder | Status |
|---|---|---|---|---|---|
| Dairy Medicine A | Medicine | 4 | bottles | 10 | 🔴 Low |
| Feed A | Feed | 2,400 | kg | 1,000 | Good |

The chain that must resolve:

```
Item → Purchase → Consumption → Balance → Reorder
```

## 12.2 Backend work required — G8.1 and G8.3

- **Item catalogue** — governed items with category, unit, reorder level and
  expiry tracking.
- **Movement ledger** — receipts and issues, with balance derived from
  movements rather than stored and mutated. The same discipline as the milking
  session ledger: the ledger is the truth, the balance is a projection.
- Medicine inventory must link to Health and Treatment, so that administering
  a treatment issues stock and a low balance raises an `INV-` finding.
- This also unblocks feed costing (§8.3).

---

# 13. Section 8 — Equipment

**Question: is the equipment available and reliable?**

**Backend readiness: WRITE-ONLY. Cannot be built as specified.**

## 13.1 Intended design

KPI row: Operational · Maintenance Due · Breakdown · Offline · Utilization.

| Equipment | Status | Last Service | Next Service | Runtime |
|---|---|---|---|---|

Equipment Profile tabs: Overview · Usage · Maintenance · Repairs · Costs ·
History.

## 13.2 Backend work required — G9.2

- `Equipment` entity with governed state (`AVAILABLE`, `IN_USE`,
  `MAINTENANCE`, `OUT_OF_SERVICE` — vocabulary already defined in
  `reference_data.py`).
- Service schedule and history, raising `EQ-` findings when maintenance falls
  due.
- Runtime and downtime capture, without which utilization and maintenance cost
  cannot be calculated.

---

# 14. Section 9 — Finance

**Question: where is the farm's money, and what is its financial position?**

**Backend readiness: PARTIAL.** Cost-of-production and reconciliation exist;
account balances do not.

## 14.1 Finance cockpit

Primary selector — Financial View: Cash Position · Daily · Monthly · Quarterly
· Yearly.

Secondary selector — Account: Cash in Hand · Money at Bank · All Accounts.

## 14.2 KPI row

Varies by selection: Cash in Hand · Money at Bank · Total Cash · Income ·
Expenses · Net Position.

## 14.3 Sections

Cash Position (visual account balances) · Income vs Expenses · Monthly,
Quarterly and Yearly Reconciliation · Expense Categories · Recent Transactions.

## 14.4 Backend work required

- **Account entity.** `FinancialTransaction` records a payment type (`CASH`,
  `BANK`, `TRANSFER`, `CARD`, `OTHER`) but there is no account and no balance.
  Cash Position cannot be computed today.
- Opening balances, and a movement ledger per account on the same pattern as
  §12.2.
- Period close and reconciliation state, so a closed month cannot silently
  change.

---

# 15. Section 10 — Cost of Production

**Question: what does a litre of milk cost us?**

**Specified in full in [AA-014 — Cost of Milk Production Design](../03_Application_Architecture/AA-014_DairyOS_Cost_of_Milk_Production_Design.md).**

It remains its own top-level section (D-UI-14), but it is an **independent
analytical calculator**: all values entered by hand, in two groups — Feed Cost
and OPEX — reading from and writing to nothing else in DairyOS (D-COP-1).

The integrated design in v1.2 was withdrawn because it depended on four things
that do not exist: the inventory ledger, purchase records, feeding-group
membership history and the finding entity. AA-014 is buildable now.

Both **cash cost** and **full economic cost** are produced, on a **whole-herd**
allocation basis, with by-product income deducted and gross and net both shown.

**Backend readiness: BUILDABLE NOW** — two small entities and a pure
calculation service, per AA-014 §13.

---

# 16. Section 11 — Records

**Question: what did the farm look like, and can I prove it?**

**Backend readiness: NOT BUILT.**

## 16.1 Intent

Records of every section above, saveable and printable, including a total
snapshot of the farm at any point in time.

## 16.2 Recommended approach

Build Records as a **replay over the persisted event journal**, not by copying
tables into snapshot rows. The event journal and operational event stream
already exist and are the only source that can answer a question about the
past without being retroactively edited.

**Honesty constraint.** A snapshot is only truthful for the period in which the
event stream is complete. For dates before the journal was in continuous use,
Records must say so rather than reconstructing a plausible figure. This is
§2.1 applied to history.

## 16.3 Backend work required

- Replay service producing a farm state as at a given timestamp.
- Export and print rendering.
- A stated "records complete from" date, surfaced in the UI.

**Open item:** whether Records also needs period-close snapshots for financial
periods, which would make month-end figures immutable. Recommended, not yet
decided.

---

# 17. Section 12 — Settings

**Backend readiness: PARTIAL.** Authentication exists; roles do not.

## 17.1 Scope

- Farm name and details; date, time and currency.
- Sign-ups and role assignment.
- Admin role with authority to hide sections per role.
- Finding and badge preferences (severity thresholds for nav badges).

## 17.2 Backend work required — G7.1

`api/auth.py` is already upgraded and issues signed bearer tokens with operator
attribution. However **five separate unwired identity trees exist in the
codebase** (`application/identity`, `core/identity`, `core/models/user.py` and
`role.py`, `operations/users`, `platform/identity`, plus
`core/security/permissions.py`). None is imported by any router.

Per decision D3: **delete all five and design identity fresh.** Do not build
role-based section visibility on any of them.

---

# 18. Backend Work Register

Everything the interface needs that does not exist. Ordered by what unblocks
the most.

## 18.1 Cross-cutting

| Item | Blocks |
|---|---|
| Operational Finding entity, ID allocator, lifecycle (§4) | Action queue, nav badges, every section's finding list |
| Per-section unresolved-count endpoint | Nav badges |
| Drop detection engine (G3.4) | Milk findings, action queue |

## 18.2 Per section

| Item | Section | Reference |
|---|---|---|
| Lifecycle vocabulary reconciliation + `CLOSE_UP` | Herd | §6.4 |
| Animal retirement path (`SOLD`, `DECEASED`) | Herd | §6.4 |
| Period aggregation endpoints | Milk | §7.7 |
| Remove `animal_id` from feed (D-UI-9) | Feed, Herd | §8.6 |
| Extend `FeedRation` for TMR stage presets | Feed | §8.4 |
| Feed endpoint consolidation | Feed | G4.2 |
| Feeding-group membership history | Feed costing | §8.5 |
| `HealthCase` entity | Health | G5.1 |
| Breeding classifier unification | Reproduction | G6.1 |
| Governed `BR-` identifiers | Reproduction | G6.6 |
| Inventory catalogue + movement ledger | Inventory, Feed costing | G8.1, G8.3 |
| `Equipment` entity + service schedule | Equipment | G9.2 |
| Worker, Task, Attendance entities | Workforce | §11.2 |
| Account entity + balances | Finance | §14.4 |
| Per-section unresolved-count endpoint (nav badges) | Cross-cutting | §4.5 |
| `CostPeriod` + `CostInput` entities, freeze, calculation service | Cost of Production | AA-014 §13 |
| Event replay service | Records | §16.3 |
| Identity and roles, built fresh | Settings | G7.1, D3 |

---

# 19. Build Sequence

Per D-UI-7, the main dashboard is first. Panels degrade gracefully where their
sections are thin; that is acceptable and informative.

1. **Main dashboard shell** — action queue and four panels, wired to what each
   domain can answer today. Panels that cannot yet be populated state so per
   §2.1.
2. **Operational Finding entity and the nav badges** — the spine the queue needs.
3. **Drop detection engine** — the first real finding producer, and the one
   that proves the pattern.
4. **Milk Production section** — including the session ledger surface (§7.6),
   which exposes work already shipped but currently invisible.
5. **Animal Profile** — closest to complete of anything remaining.
6. **Herd Dynamics** — after the vocabulary reconciliation.
7. **Health**, after `HealthCase`.
8. **Reproduction**, after classifier unification.
9. **Inventory ledger**, then the Inventory section, then feed costing.
10. **Equipment**, **Workforce**, **Finance accounts**.
11. **Records**, last, once the event stream it replays is stable.

---

# 20. Open Items

Not blocking, but undecided:

- **Panel display options.** The design allows each dashboard panel a choice of
  presentations. Recommendation: ship fixed defaults, make one panel
  configurable, and observe whether anyone changes it before building four.
- **Threshold configurability.** Drop thresholds are fixed at 20% / 10% per
  D-UI-3. Whether they become farm-configurable in Settings is deferred until
  the feature has been used.
- **Period-close snapshots** for financial periods (§16.3).
- **`SICK` as a lifecycle status.** With `CLOSE_UP` confirmed as a stage, it is
  still unresolved whether `SICK` is a lifecycle stage or a health state
  overlaid on a lifecycle. Recommendation: health state, not lifecycle.

---

*End of AA-013.*
