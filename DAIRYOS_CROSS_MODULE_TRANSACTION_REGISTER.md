# DairyOS Cross-Module Transaction Register

| Business action | Required consistency boundary | Current state |
| --- | --- | --- |
| Payroll payment to Finance posting | One database transaction with idempotent link and one active Finance posting per Payroll record | Implemented and regression-certified |
| Milk sale / Finance commercial amendment and VOID propagation | One bidirectional atomic database transaction so linked `FinancialTransaction` and `MilkDisposition` cannot diverge | Implemented and regression-certified |
| Breeding/calving propagation | One transaction or durable outbox | Remains a remediation requirement where propagation is not already transactionally coupled |
| TMR materialisation | Deterministic source identity with database uniqueness | Remains an integrity requirement |

For Finance-linked milk sales, both permitted amendment entry points operate on
the same governed commercial fact. Quantity, counterparty, governed rate,
amount due and lifecycle/VOID state must remain synchronized across the
primary Finance transaction and its linked Milk disposition.

Log-only failure handling is not completion. Any deferred secondary
projection requires durable retry state and an operator-visible degraded
condition.
