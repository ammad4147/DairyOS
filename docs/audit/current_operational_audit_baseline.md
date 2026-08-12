# DairyOS Current Operational Audit Baseline

**Authoritative branch:** `recovery-execution`

**Baseline rule:** current repository evidence and executable tests override historical replacement lists and planning notes.

## Current remediation disposition

| Finding / capability | Current disposition |
|---|---|
| AUD-001 active UI/runtime surface ambiguity | CLOSED — FastAPI root identifies React/Vite as authoritative and retired static UI is not served |
| AUD-013 stale UI verification contract | CLOSED — active-shell tests now target the React/Vite surface |
| C-03 veterinary treatment/withdrawal | SUBSTANTIALLY CLOSED — persisted treatment plus withdrawal safety contract is present |
| H-07 persistent operational repositories | SUBSTANTIALLY CLOSED — PostgreSQL repositories are composed through RepositoryFactory |
| Animal ID permanence | CLOSED for registration path — server generates `AN-*`; operator-supplied permanent ID rejected |
| AUD-012 backup/disaster recovery | IMPLEMENTED — native PostgreSQL backup/restore with manifest checksum and automated safety tests; production restore drill remains an operational deployment requirement |
| AUD-002 lifetime Animal Passport | IMPLEMENTED FOUNDATION — persisted cross-domain passport endpoint now exposes animal, milk, health, breeding, treatment and operational-event history |
| AUD-004 milk traceability | OPEN — persistence and Animal-ID linkage exist; complete traceability/chain-of-custody contract still requires explicit reconciliation of milking events, operator, session, period and downstream aggregation |
| H-02 calf/youngstock | IMPLEMENTED FOUNDATION — persisted CALF/HEIFER selection and age/parentage projection exists; management workflows remain incomplete |
| H-03 reproduction | IMPLEMENTED FOUNDATION — persisted breeding events exist; complete reproductive lifecycle and outcome validation remain open |
| H-04 professional nutrition | OPEN — feed records exist; full requirement/nutrient/ration/intake/cost engine is not demonstrated |
| H-05 cost of production | OPEN — current KPI endpoint derives a basic expense-per-litre measure; full cost allocation engine remains open |
| H-06 standard dairy KPI engine | IMPLEMENTED FOUNDATION — live persisted KPI endpoint exists; metric catalogue, definitions, validation and complete dairy KPI coverage remain open |
| S-03 heat stress | IMPLEMENTED FOUNDATION — persisted THI observations and risk classification exist; farm-wide intervention intelligence remains open |
| S-04 welfare KPI system | IMPLEMENTED FOUNDATION — persisted health/treatment-derived welfare KPIs exist; broader welfare framework remains open |
| S-05 SOP/protocol engine | IMPLEMENTED FOUNDATION — persisted versioned protocol records exist; execution/compliance/acknowledgement workflow remains open |
| AUD-006 reference/master-data governance | OPEN — meaningful choices exist, but authoritative reference-data lifecycle is not yet uniform |
| AUD-014 ApplicationRuntime complexity | REVIEW — composition is consolidated; further responsibility-boundary review is lower priority than incomplete operational domains |

## Execution queue

1. AUD-004 — Milk traceability completeness
2. AUD-006 — Reference/master-data governance
3. H-03 — Reproductive lifecycle completeness
4. H-04 — Professional nutrition engine
5. H-05 — Cost-of-production engine
6. H-06 — KPI catalogue/validation completeness
7. S-03 — Heat-stress intervention intelligence
8. S-04 — Welfare framework completeness
9. S-05 — SOP execution/compliance workflow
10. AUD-014 — Runtime responsibility-boundary review

Dashboard visual refinement remains deferred until this queue is complete.

## Verification rule

A finding closes only when implementation, persistence/linkage, tests, and local operational verification agree. A route or model existing by itself is not evidence of completion.
