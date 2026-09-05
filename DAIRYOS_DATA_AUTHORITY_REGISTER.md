# DairyOS Data Authority Register

| Fact | Governed authority | Persistent projections / consumers |
| --- | --- | --- |
| Finance transaction and settlement | `FinancialTransaction` | Finance ledger and dashboard totals |
| Milk production | `MilkProduction` | Dashboard, reconciliation and profitability metrics |
| Milk sale identity | `MilkDisposition.sale_id` | Finance-linked commercial and settlement records |
| Finance-originated primary milk sale | `MilkDisposition.sale_id = FIN-{FinancialTransaction.id}` | Primary sale `FinancialTransaction` plus `MilkDisposition` |
| Subsequent financial postings for a milk sale | `FinancialTransaction.milk_sale_id = MilkDisposition.sale_id` | Receipts and other governed linked postings |
| Official monthly COP | `COMLRecord` | COP presentation |

## Milk sale consistency invariant

A Finance-linked milk sale has one commercial fact represented by both the
primary `FinancialTransaction` and the linked `MilkDisposition`.

Permitted Finance and Milk amendment entry points must invoke one atomic
consistency boundary. The linked records may not disagree on governed
quantity, counterparty, unit/per-litre rate, amount due or lifecycle status.

`FinancialTransaction.milk_sale_id` is not the primary Finance sale's
back-reference. It identifies subsequent financial postings that refer to the
`MilkDisposition.sale_id`.

VOID is retained historical evidence and is excluded from active accounting
totals by the canonical transaction classifier.
