# DairyOS — Forensic Audit Status

**Audit date:** 19 August 2026  
**Repository:** `ammad4147/DairyOS`  
**Branch:** `post-dashboard-reconciliation`  
**Audit authority:** current repository evidence at this branch

## 1. Acceptance rule

A capability is considered operational only when the representative path demonstrates:

`real input -> validation -> durable persistence -> attribution -> operational state -> intelligence/decision where applicable -> authoritative UI projection -> auditable history`.

A green isolated test is evidence, not by itself an end-to-end closure.

## 2. Current findings

| ID | Finding | Current status | Evidence / remaining gate |
|---|---|---|---|
| F-016 | Operational input persistence/event ordering | CLOSED | Repository-backed persistence precedes operational event publication; full regression remains green. |
| F-005 | Animal -> milk -> history -> authoritative UI traceability | PARTIALLY CLOSED | Permanent Animal ID enforcement, Passport projection, and React Passport UI are present. Local representative end-to-end execution is still required before final closure. |
| F-004 | Lifetime animal passport does not converge relevant history | CLOSED AT CODE LEVEL | `LifetimeAnimalPassportService` projects milk, health, breeding, treatments, feed, finance, operational events, timeline, and effective schedule through an optional operational date; React consumes `/farm/animals/{animal_id}/passport`. |
| F-017 | Operator attribution not consistently server-authoritative | CONDITIONAL / CONTROLLED | Authenticated bearer identity overrides client `operator`; invalid tokens cannot fall back. Anonymous local/operator writes remain intentionally supported for the existing local UI contract. Production deployment must decide whether anonymous writes are disabled. |
| F-018 | Environment-coupled frontend API addressing | CLOSED AT CODE LEVEL | Frontend API resolution uses runtime override, build configuration, page origin, and development fallback; literal host addressing is centralized. |
| F-003 | Backup/restore/disaster recovery | OPEN — LOCAL ACCEPTANCE REQUIRED | Native `pg_dump`/`pg_restore` utility and recovery runbook exist, but a real backup -> restore -> application acceptance cycle has not been evidenced by repository inspection. |
| CMP | CMP capability lacked authoritative UI projection | CLOSED AT CODE LEVEL | Settings now consumes `/farm/cmp/scenarios` for persisted scenarios and `/farm/cmp/scenarios` POST for creation; displayed CMP values are backend results, not frontend calculations. |

## 3. Route-contract finding resolved

FastAPI 0.140+ keeps included routers behind `_IncludedRouter` wrappers. Direct `app.routes` inspection therefore does not expose the mounted application paths. The analytics and reconciled-capability tests now use `app.openapi()["paths"]`, which is the application-level route surface used for these contract assertions.

Acceptance already demonstrated on the local checkout:

- targeted route-contract tests: `10 passed`
- full regression: `1853 passed, 1 skipped`
- `git diff --check`: clean apart from normal Windows LF/CRLF warnings
- remote branch was synchronized after commit `f6d6a1bef293b974ddc3fed789d25062a698ec24`

## 4. Current backend authority

The reconciled capability registry now records these audited capabilities as `LIVE`:

- farm identity/settings
- animal passport
- effective-dated milking schedule
- milk execution/intelligence
- milk reconciliation
- milk dispositions
- analytics contract
- CMP scenarios
- dashboard read model

`frontend_calculation_authority` remains `false`.

## 5. Required local acceptance before repository reconciliation

Run from `D:\DairyOS` after fetching the current remote branch:

```powershell
git fetch origin
git checkout post-dashboard-reconciliation
git reset --hard origin/post-dashboard-reconciliation
$env:PYTHONPATH = "$PWD\src"

pytest -q
python -m compileall -q src

Set-Location "src\DairyOS.Web"
npm ci
npm run build
Set-Location "D:\DairyOS"

python scripts/database_backup.py backup --output backups\forensic-acceptance.dump
python scripts/database_backup.py verify --input backups\forensic-acceptance.dump
```

For F-003 closure, restore that dump into a disposable PostgreSQL database, run the DairyOS readiness check against the restored database, and verify that representative persisted records remain readable. Do not restore over the production database for this acceptance test.

For F-005 closure, demonstrate one representative path locally:

`create Animal -> obtain permanent animal_id -> record milk -> retrieve Passport -> observe milk history/timeline -> retrieve milk intelligence -> verify the React Passport/operational UI displays the persisted record`.

For F-017 closure, authenticate through `/login`, submit a farm write with a deliberately different client `operator`, and verify the persisted/resulting attribution is the authenticated `sub`. Then make the explicit deployment decision whether anonymous farm writes are permitted in the intended production environment.

## 6. Audit conclusion

No further remote production defect was identified during this audit pass after the route-contract correction and the capability/UI reconciliation. The remaining blockers are **local runtime evidence gates**, not requests to provide source files: F-003 backup/restore acceptance, F-005 representative end-to-end animal/milk/UI execution, and the final production policy decision for anonymous writes under F-017.

The local checkout must be reconciled to the exact remote branch tip after the local acceptance run; any local divergence must be investigated rather than overwritten blindly.
