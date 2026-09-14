# System Health v2 — FC-SIM Suitability Matrix

Assessment baseline: `df521837c812b03b2cb9dd8df434c9816ee7a908`.
System Health execution is read-only and must report evidence, never repair farm state.

| SIM | Candidate invariant | Current authority / coverage | Suitability and disposition | Check / verification |
|---|---|---|---|---|
| SIM-A | Animal category is canonical | Animal Register classification service and six-category tests | Extend existing; useful persisted-state integrity check | `SH-A-001`; healthy, unknown-category, read-only tests |
| SIM-A | Active category totals reconcile with Animal Register | Animal repository and dashboard projections | Implement new; cross-module reconciliation | `SH-A-002`; totals and empty-herd tests |
| SIM-A | Passport category/identity agrees with Animal authority | Passport projection and animal repository | Implement new; no duplicate operator alert | `SH-A-003`; mismatch/orphan tests |
| SIM-A | Duplicate animal identity / wrong-history attribution | Database constraints and passport history | Extend existing; detect residual historical inconsistency | `SH-A-004`; duplicate/orphan fixtures in disposable DB |
| SIM-M | Duplicate animal/date/session | Milk session authority and database constraints | Merge with existing; integrity result, not duplicate warning | `SH-M-001`; duplicate and boundary tests |
| SIM-M | Session totals reconcile with daily biological totals | Milk production/session repositories | Implement new; calculation reconciliation | `SH-M-002`; daily aggregation tests |
| SIM-M | Invalid session/date relationship | Operational date authority and milk lifecycle | Implement new; read-only temporal integrity | `SH-M-003`; future/date-boundary tests |
| SIM-M | Milk destination/disposition balance | Milk disposition authority and reconciliation service | Extend existing; consume canonical warning result | `SH-M-004`; saleable/withdrawal/carry tests |
| SIM-M | Withdrawal milk enters ordinary saleable milk | Milk disposition and Health withdrawal bridge | Implement new; cross-module integrity | `SH-M-005`; withdrawal exclusion tests |
| SIM-M | Milk denominator agrees with COML/COP | COP/COML period authority | Merge with COP checks | `SH-M-006`; same-period denominator tests |
| SIM-F | Required daily TMR authority missing/duplicated | TMR daily snapshot authority | Implement new; distinguish `AUTHORITY_MISSING` from failure | `SH-F-001`; missing/duplicate snapshot tests |
| SIM-F | Snapshot population agrees with Animal Register | TMR snapshot and category authority | Implement new; cross-module reconciliation | `SH-F-002`; six-category population tests |
| SIM-F | Ration × population and ingredient arithmetic | Governed ration/formulation authority | Implement new; independent arithmetic using canonical inputs | `SH-F-003`; arithmetic/boundary tests |
| SIM-F | TMR cost arithmetic | Frozen ingredient prices and snapshot totals | Implement new; calculation reconciliation | `SH-F-004`; price/rounding tests |
| SIM-F | Expected SYSTEM_TMR materialisation | Feed Storage movement authority | Extend existing; no failure when no feed was purchased and current semantics require no movement | `SH-F-005`; purchased/no-purchase cases |
| SIM-F | Materialised movement/date/history agrees with snapshot | Feed Storage and TMR history | Implement new; cross-module reconciliation | `SH-F-006`; operational-date/idempotency tests |
| SIM-$ | Sale quantity × rate and orphan references | Finance transaction authority | Implement new; calculation/reference reconciliation | `SH-$-001`; quantity/rate/orphan tests |
| SIM-$ | Feed price and semen inventory attribution | Finance, Feed, Semen authorities | Implement new where source references exist | `SH-$-002`; linked/unlinked tests |
| SIM-$ | Equipment purchase excluded from OPEX | OPEX classification authority | Extend existing COP/OPEX reconciliation | `SH-$-003`; classification tests |
| SIM-$ | VOID excluded from active totals | Finance ledger authority | Extend existing; integrity check only | `SH-$-004`; VOID totals tests |
| SIM-C | Feed Cost/L, OPEX/L, COP/L arithmetic and periods | Canonical COML/COP services | Merge with existing calculation authority; no parallel formula | `SH-C-001`; null denominator and period tests |
| SIM-C | Historical authority missing or replaced by present authority | TMR snapshots, period milk and finance authorities | Implement new; `AUTHORITY_MISSING`/`ATTENTION` | `SH-C-002`; historical snapshot tests |
| SIM-B | AI/PD/pregnancy/calving/loss structural integrity | Breeding cycle projection and canonical analytics | Extend existing; structural checks only | `SH-B-001`; lifecycle sequence tests |
| SIM-B | Dashboard ratio agrees with canonical ratio | Breeding analytics service | Merge with existing canonical Pregnancy Ratio | `SH-B-002`; projection equality tests |
| SIM-B | Semen lot consumption agrees with AI | Semen inventory and breeding records | Implement new where lot authority is present | `SH-B-003`; linked/unlinked tests |
| SIM-H | Health observation/case/treatment orphan or cross-animal links | Health repositories and database constraints | Extend existing as detective control; API/transaction atomicity and same-animal validation remain the preventive production invariant and are not closed by this check | `SH-H-001`; orphan/cross-animal tests |
| SIM-H | Health withdrawal agrees with Milk | Health withdrawal bridge and Milk disposition | Implement new; cross-module reconciliation | `SH-H-002`; withdrawal-period tests |
| SIM-H | Health projection agrees with Passport | Passport health projection | Implement new; projection reconciliation | `SH-H-003`; history/projection tests |
| SIM-V | Schedule authority agrees with Dashboard projection | Schedule-first vaccination projector | Implement new; reject duplicate overdue reminders | `SH-V-001`; due/overdue/completed tests |
| SIM-V | Due-today, missed, and future schedule boundaries | Operational date authority and vaccination projector | Extend existing; temporal reconciliation | `SH-V-002`; boundary tests |
| SIM-X | Cross-module operational date agreement | Farm operational date authority | Implement new; high-value integrity check | `SH-X-002`; fixed-date and transition tests |
| SIM-X | Animal ↔ TMR ↔ Milk ↔ COP ↔ Finance authority chain | Canonical module services above | Implement as targeted reconciliation checks that consume and compare canonical authorities; never maintain a shadow ledger or competing formula | `SH-X-003`; cross-module disposable fixtures |
| SIM-N | Invalid/orphan/impossible persisted states | Database constraints plus checks above | Certification-only for creating invalid inputs; detection is implementable | Covered by domain checks; no production mutation |
| SIM-N | Zero milk denominator / missing TMR authority | COP/TMR authority services | Implement new with nullable/incomplete semantics, never fabricated zero | `SH-C-002`; missing-authority tests |
| SIM-N | Duplicate TMR materialisation / repeated PD state | TMR idempotency and breeding cycle authority | Extend existing; persisted-state reconciliation | `SH-F-006`, `SH-B-001`; idempotency tests |

## Deliberately rejected or deferred candidates

- Routine overdue vaccination, health, and production reminders are `DUPLICATE_REJECTED` when Dashboard already owns the operator alert. System Health checks authority/projection disagreement instead.
- Invalid-input creation scenarios are `CERTIFICATION_ONLY`; System Health never creates bad farm records.
- TMR `CALCULATED + zero consumption = FAIL` is not implemented as a blanket rule. With no purchased feed, the established authority permits no Feed Storage materialisation.
- Raw combined twice-/thrice-daily yield normalization is `SUPERSEDED`; the approved design ranks the two cohorts separately.
- A second Pregnancy Ratio formula is `CONFLICT_REJECTED`; the canonical breeding analytics authority is reused.
- Historical FC-SIM assumptions superseded by schedule-first Vaccination and current operational-date authority are `SUPERSEDED`.

## Status semantics

Checks use the existing `PASS`/`WARNING`/`FAIL` response contract. Where an authority is absent, the implementation must expose an explicit authority-missing condition in evidence and must not report mathematical `PASS` merely because it had nothing to calculate.

## Preventive versus detective controls

System Health is detective. It identifies residual, historical, or projection-level corruption and reports evidence; it does not repair records and does not replace preventive API, transaction, database-constraint, or outbox guarantees. In particular, `SH-H-001` can detect residual evidence related to TX-04 and HEALTH-01, but those production findings require separate verification that new writes are prevented atomically and cannot cross animal ownership boundaries.
