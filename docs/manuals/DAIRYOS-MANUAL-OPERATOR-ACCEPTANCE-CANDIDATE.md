# DairyOS Manual Operator Acceptance Candidate

Status: discovery and register phase; not yet an execution-certified manual.

Candidate source commit: `c444778a320bc718d06a6c4528c76d8ca7bb8532`

Candidate source tree: `b77bb3632d09a695729e5243b1a47b20e43288e1`

This program must be executed only against a clean certification installation or a disposable acceptance farm. It must never be run against valuable operational farm data.

## 1. Operator surface register

| Surface ID | Current surface | Primary operator actions | Immediate authority | Downstream verification |
|---|---|---|---|---|
| SUR-DASH | Unified Dashboard | choose chart range, cohort/range controls, open alerts, yield-drop comparison, production extremes, open Passport/module | dashboard read model | Dashboard, Passport, Milk, Health, Breeding, Analytics |
| SUR-ANI | Animals | register animal, search/filter, open Passport | animal register | herd counts, Passport, lineage, Milk eligibility |
| SUR-PAS | Animal Passport | edit supported identity fields, add photo, record mortality, inspect projections | animal/lifecycle register | Milk, Health, Vaccination, Breeding, lineage, history |
| SUR-MIL | Milk | record sessions, explicit zero, not-milked reason, amend/void, quality sample, disposition, reconciliation, export | governed Milk ledger and disposition authority | Milk history, Passport, Dashboard, Analytics, Reporting, Finance |
| SUR-FED | Feed | inspect storage, adjust stock, record usage where exposed, inspect equipment, refresh governed data | Feed storage and Finance-linked purchase authority | Feed balance, TMR, Finance, COML, alerts |
| SUR-TMR | TMR Preparation | choose category/stage, enter ration ingredients/quantities, save/version, review/materialize where exposed | governed TMR preference/snapshot authority | Feed cost, COML, Dashboard, Reporting |
| SUR-FIN | Finance | record revenue/expense/purchase, animal purchase/sale, semen purchase, edit, settle, void, payroll entry if reachable | financial transaction ledger | balances, Feed, Semen, Animal, Milk, COML, Reporting |
| SUR-BRD | Breeding | semen lot selection, AI, PD, calving, loss, planned return | breeding event and reproductive-state authority | Passport, herd/lifecycle, calves, Analytics, Dashboard |
| SUR-HLT | Health | clinical case/treatment, diagnosis, symptoms, medication, withdrawal, follow-up | clinical/treatment and withdrawal authority | Health log, Milk restriction, Passport, alerts |
| SUR-VAC | Vaccination | schedule, amend, administer/mark given, void, search/filter | vaccination schedule/history authority | due/overdue state, Dashboard, Passport, Reporting |
| SUR-COM | COML | choose period and governed assumptions/controls exposed by UI | governed cost-of-milk calculation | Dashboard, Feed, Finance, Reporting |
| SUR-ANA | Analytics | select period and available filters | analytics read models | deterministic charts/tables and source records |
| SUR-RPT | Reporting | choose area/report/period/date/as-of/filter/columns, sort, drill, export | report-specific authority | report rows, totals, reconciliation, exported file |
| SUR-SET | Settings | farm profile, prefix, operational settings, dashboard preferences, navigation visibility, email/system controls | settings authority | persisted settings and downstream behavior after restart |
| SUR-DAT | Data controls | export/import and operator-accessible backup/restore/health/status actions | governed data-management/recovery authority | files, integrity/status, restart and recovery behavior |
| SUR-AUD | Audit/alerts | inspect active warnings, audit register, acknowledge/resolve where exposed | operational finding authority | Dashboard alerts, histories, audit records |

## 2. Entry-point register

This is the first controlled register. Each row becomes one or more permanent `MAN-*` scenarios after field-level review.

| Entry ID | Surface | Entry/action | Required coverage class | Result authority | Planned scenario |
|---|---|---|---|---|---|
| ENT-ANI-001 | Animals/Passport | register adult animal | positive, missing fields, duplicate identity | animal register | MAN-ANI-001 |
| ENT-ANI-002 | Animals/Passport | register calf with dam | positive, missing/invalid dam | animal register and lineage | MAN-ANI-002 |
| ENT-ANI-003 | Passport | edit identity, ear tag, RFID, breed, dates, location, group | positive and invalid dates/relationships | animal register | MAN-PAS-001 |
| ENT-ANI-004 | Passport | set milking frequency | TWICE_DAILY/THRICE_DAILY and invalid state | milking schedule authority | MAN-ANI-003 |
| ENT-ANI-005 | Passport | record mortality | positive, required fields, inactive preservation | lifecycle/exit authority | MAN-PAS-002 |
| ENT-MIL-001 | Milk | record morning/evening session | positive, duplicate, missing session | Milk session ledger | MAN-MIL-001 |
| ENT-MIL-002 | Milk | record afternoon session | thrice-daily positive and wrong-frequency rejection | Milk session ledger | MAN-MIL-002 |
| ENT-MIL-003 | Milk | explicit zero/not milked | positive, required governed reason | Milk ledger | MAN-MIL-003 |
| ENT-MIL-004 | Milk | amend/void production | correction and audit | Milk ledger | MAN-MIL-004 |
| ENT-MIL-005 | Milk | quality sample | positive, invalid values | quality authority | MAN-MIL-005 |
| ENT-MIL-006 | Milk | disposition/saleable reconciliation | positive, over-allocation rejection | disposition authority | MAN-MIL-006 |
| ENT-FED-001 | Finance/Feed | feed purchase to stock | quantity/rate and non-positive rejection | Finance plus Feed storage | MAN-FED-001 |
| ENT-FED-002 | Feed | stock adjustment/usage | positive, insufficient/negative stock | Feed storage | MAN-FED-002 |
| ENT-TMR-001 | TMR | category/stage ration | ingredient, quantity, unit, save/version | TMR authority | MAN-FED-003 |
| ENT-FIN-001 | Finance | expense categories and OPEX classification | every current UI category | Finance ledger | MAN-FIN-001 |
| ENT-FIN-002 | Finance | Milk Sales | quantity × governed rate, disposition linkage | Finance/Milk | MAN-FIN-002 |
| ENT-FIN-003 | Finance | animal purchase/sale | category and Passport linkage | Finance/Animal | MAN-FIN-003 |
| ENT-FIN-004 | Finance | semen purchase | lot, supplier, type, straws, cost | Finance/Semen inventory | MAN-BRD-001 |
| ENT-FIN-005 | Finance | edit/settle/void | state transition and idempotency | Finance ledger | MAN-FIN-004 |
| ENT-FIN-006 | Finance/Payroll | payroll entry if operator reachable | reachability and posting | payroll/Finance | MAN-FIN-005 |
| ENT-BRD-001 | Breeding | AI using purchased semen lot | valid and unavailable-lot rejection | breeding event/state | MAN-BRD-002 |
| ENT-BRD-002 | Breeding | PD positive/negative | state transition and cycle closure | reproductive state | MAN-BRD-003 |
| ENT-BRD-003 | Breeding | calving and planned return | confirmed pregnancy requirement | lifecycle/offspring | MAN-BRD-004 |
| ENT-BRD-004 | Breeding | pregnancy loss | valid state and invalid-state rejection | reproductive state | MAN-BRD-005 |
| ENT-HLT-001 | Health | clinical treatment/case | required fields and invalid animal | health authority | MAN-HLT-001 |
| ENT-HLT-002 | Health | withdrawal and follow-up | withdrawal date and due state | treatment/withdrawal | MAN-HLT-002 |
| ENT-VAC-001 | Vaccination | schedule | required fields and dates | vaccination schedule | MAN-VAC-001 |
| ENT-VAC-002 | Vaccination | amend/administer/void | state transitions and history | vaccination authority | MAN-VAC-002 |
| ENT-SET-001 | Settings | farm profile/prefix | persistence and invalid values | settings authority | MAN-SET-001 |
| ENT-SET-002 | Settings | operational date/time settings | historical/future/date-boundary behavior | date authority | MAN-SET-002 |
| ENT-SET-003 | Settings | navigation visibility | hide/show persistence without data deletion | settings authority | MAN-SET-003 |
| ENT-RPT-001 | Reporting | report area/report/period/filter/columns | deterministic rows/totals/export | report authority | MAN-RPT-001 |
| ENT-DAT-001 | Data | export/import | portable state and integrity | data-management authority | MAN-DAT-001 |
| ENT-DAT-002 | Data/System | backup/restore/health/status | safe recovery and non-destructive behavior | recovery authority | MAN-DAT-002 |

## 3. Controlled farm story

Use a disposable farm named `MOT Acceptance Farm`. Do not hand-edit permanent DairyOS IDs. Register records through the UI and retain the generated IDs in the operator worksheet, adding MOT labels in the available legacy ID, ear tag, or notes fields.

The minimum controlled set is:

- two active milking animals, one TWICE_DAILY and one THRICE_DAILY;
- one withdrawal animal;
- one breeding animal for successful calving;
- one breeding animal for pregnancy loss;
- one dry animal;
- one heifer;
- one female calf and one male calf;
- one bull;
- one animal reserved for yield-drop comparison;
- one animal reserved for exit/mortality verification.

The final worksheet will record generated permanent IDs, dates, categories, frequencies, relationships, and all independently calculated expected totals before operator execution.

## 4. Output and calculation register

| Output ID | Surface | Output to verify | Independent expected-value method |
|---|---|---|---|
| OUT-ANI-001 | Animals/Dashboard | category and total herd counts | count controlled records by current lifecycle/category rules |
| OUT-MIL-001 | Milk/Passport | daily session and total milk | sum exact entered sessions; verify frequency completion |
| OUT-MIL-002 | Milk | reconciliation and closing balance | produced − each governed disposition |
| OUT-MIL-003 | Dashboard | current/prior yield and drop percentage | `(prior-current)/prior × 100` |
| OUT-FED-001 | Finance/Feed | purchase quantity, rate, stock, balance | opening + purchases − governed usage ± adjustments |
| OUT-TMR-001 | TMR/COML | ration and per-head cost | sum ingredient quantity × governed rate ÷ applicable head count |
| OUT-FIN-001 | Finance | amount, status, balance, settlement | independently calculate quantity × rate and ledger transitions |
| OUT-BRD-001 | Breeding/Passport | AI, PD, pregnancy, loss/calving, cycle | event sequence and current-state rules from current UI authority |
| OUT-HLT-001 | Health/Milk | treatment, follow-up, withdrawal | entered withdrawal policy and governed end date |
| OUT-VAC-001 | Vaccination/Passport | scheduled, due, overdue, administered, void | scheduled date versus controlled operational date |
| OUT-RPT-001 | Reporting | report rows, totals, filters, exports | reconcile report values to controlled source story |
| OUT-DAT-001 | Data | export/import/restore result | compare post-import/recovery visible records and checksums |

## 5. Reconciliation rules before execution

1. Every field and actionable button discovered in the current installed build must map to an `ENT-*` row or be classified as non-business navigation.
2. Every operator-visible metric, status, history, report, export, and cross-module projection must map to an `OUT-*` row and a scenario.
3. Every scenario must contain preconditions, exact inputs, independently derived expected values, verification locations, restart verification where applicable, PASS/FAIL/BLOCKED, actual result, notes, and defect reference.
4. Any source/UI mismatch is a coverage gap or product defect, never an invented manual test.
5. This candidate must be versioned with the exact source/build and re-reviewed after any later `main` change.
