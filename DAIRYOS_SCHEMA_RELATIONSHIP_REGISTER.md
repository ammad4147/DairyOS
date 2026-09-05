# DairyOS Schema Relationship Register

Schema constraints are introduced only after a disposable restored-database
census establishes that historical records satisfy them. Each proposed link
must be classified as an internal relationship, external identifier,
historical reference or derived projection key before a foreign key or other
database-enforced integrity rule is added.

## Current remediation chain

| Revision | Schema authority |
| --- | --- |
| `20260905_00` | Brings the current Finance-owned Payroll schema under Alembic authority additively and non-destructively. |
| `20260905_01` | Converts governed Finance, Milk-commercial and official COP monetary/rate scalar columns from binary floating point to fixed-point `NUMERIC`. |
| `20260905_02` | Enforces at most one non-VOID active Finance posting per Payroll record through a partial unique index. |
| `20260905_03` | Adds nullable `semen_or_bull` and `notes` columns to `breeding_records` so operator-entered breeding details remain in PostgreSQL authority. |
| `20260905_04` | Adds `breeding_propagation_outbox` for durable, retryable, idempotent Breeding/calving propagation to non-transactional operational-input/event projections. |

The current remediation chain does not introduce a new foreign key.

The Payroll/Finance active-posting constraint is enforced by database
uniqueness rather than by a new foreign-key relationship. Historical VOID
Finance postings remain permissible and retained for audit history.

Any future foreign key, cascade rule or destructive-operation constraint must
still pass the disposable-database census and migration replay gates before it
is considered safe for the production schema.
