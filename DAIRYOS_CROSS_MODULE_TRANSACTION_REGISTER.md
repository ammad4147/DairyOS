# DairyOS Cross-Module Transaction Register

| Business action | Required consistency boundary | Current state |
| --- | --- | --- |
| Payroll payment to Finance posting | One database transaction with idempotent link and one active Finance posting per Payroll record | Implemented and regression-certified |
| Milk sale / Finance commercial amendment and VOID propagation | One bidirectional atomic database transaction so linked `FinancialTransaction` and `MilkDisposition` cannot diverge | Implemented and regression-certified |
| Breeding/calving propagation | PostgreSQL Breeding/Animal mutation plus durable propagation outbox; deterministic event identity and retry to operational-input/event projections | Implemented; local/CI certification required |
| TMR materialisation | Deterministic source identity with database uniqueness | Remains an integrity requirement |

For Finance-linked milk sales, both permitted amendment entry points operate on
the same governed commercial fact. Quantity, counterparty, governed rate,
amount due and lifecycle/VOID state must remain synchronized across the
primary Finance transaction and its linked Milk disposition.

Log-only failure handling is not completion. Any deferred secondary
projection requires durable retry state and an operator-visible degraded
condition.
