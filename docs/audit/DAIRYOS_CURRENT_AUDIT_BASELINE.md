# DairyOS Current Operational Audit Baseline

Baseline established against `recovery-execution` during the August 2026 recovery audit. This document is the authoritative remediation register; historical replacement numbering and prior capability lists are evidence only.

## Closure standard

A finding is closed only when implementation, persistence, integration, tests and operational verification all support the claim. A commit alone does not close a finding.

## Findings and remediation

| ID | Finding | Disposition |
|---|---|---|
| AUD-001 | Two operator UI surfaces existed and could diverge | Remediated: FastAPI no longer serves the retired static operator UI; React/Vite is declared authoritative |
| AUD-002 | Lifetime Animal Passport incomplete | Remediated foundation: persisted cross-domain passport endpoint now aggregates animal, lifecycle, milk, feed, health, breeding, treatment and finance history |
| AUD-003 | Persistent operational repositories | Closed/substantially implemented; RepositoryFactory owns PostgreSQL-backed adapters |
| AUD-004 | Milk traceability insufficiently proven | Remediated: animal-linked writes require an existing permanent Animal ID and passport exposes persisted milk history |
| AUD-005 | Treatment/withdrawal safety | Closed/substantially implemented; maintained drug reference and withdrawal enforcement retained |
| AUD-006 | Reference/master-data governance incomplete | Remediated foundation: central `/farm/reference-data` catalog distinguishes persisted choices from governed vocabularies |
| AUD-007 | Cost-of-production engine incomplete | Remediated foundation: persisted expense and milk data produce transparent cost/litre and category breakdown |
| AUD-008 | Reproduction lifecycle incomplete/unproven | Remediated foundation: persisted reproductive status endpoint derives heat, insemination, pregnancy, calving and expected-calving state |
| AUD-009 | Calf/youngstock management not demonstrated | Remediated foundation: `/farm/youngstock` exposes persisted calf/heifer population and lifecycle data |
| AUD-010 | Professional feed/nutrition incomplete | Remediated foundation: persisted ration-plan engine plus live feed records; no nutritional values are fabricated |
| AUD-011 | Standard dairy KPI engine incomplete | Remediated foundation: live persisted herd, milk, feed, financial, health and reproduction KPIs with explicit quality status |
| AUD-012 | Backup/disaster recovery not demonstrated | Remediated: native PostgreSQL backup/verify/restore utility and recovery runbook added |
| AUD-013 | Tests validated retired UI contract | Remediated: operator UI tests now validate React/Vite source and API contract instead of legacy static HTML |
| AUD-014 | ApplicationRuntime complexity | Reviewed; no functional change required in this pass; composition boundary remains explicit |
| S-03 | Heat-stress intelligence absent | Remediated foundation: persisted environmental observations, THI calculation and severity alerts |
| S-04 | Welfare KPI system absent | Remediated foundation: persisted morbidity, mortality and treatment-rate KPIs |
| S-05 | SOP/protocol engine absent | Remediated foundation: versioned persisted SOP protocol records with active state |

## Historical remediation reconciliation

The former 31-file replacement sequence is no longer the execution authority. Each historical replacement must be classified against the findings above as closed, superseded, partial, open or invalidated. No historical replacement is reopened solely because its number was next.

## Remaining verification

The repository changes in this baseline require the local authoritative verification pass: pull `recovery-execution`, run the complete pytest suite, build the React/Vite frontend, run the local API, exercise persistence against the configured PostgreSQL database, and perform a backup/restore drill using the documented utility.
