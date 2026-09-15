# Reporting backend authority

The Reporting API is a read-only projection over existing DairyOS persistence authorities. It does not create a second reporting ledger.

| Reporting domain | Backend authority |
| --- | --- |
| Animals | Animal repository and governed category classifier |
| Milk | MilkProduction repository; disposition repository; Milk Quality repository |
| Feed / TMR | Feed ration repository and historical persisted ration records |
| Finance | FinancialTransaction repository and canonical transaction classifier |
| Breeding | Database breeding repository |
| Semen | Finance purchase rows reconciled with breeding semen-lot usage |
| Health | Health Case and Treatment repositories |
| Vaccination | Vaccination repository |
| COML / COP | COML repository |
| Whole Farm | Cross-domain projections at the requested snapshot date |

Reporting uses Farm Operational Date authority for period resolution. Missing values remain missing; explicit numeric zero remains zero. VOID Finance rows remain visible to audit output while the canonical classifier excludes them from active operating totals. Milk session selection preserves MORNING, AFTERNOON and EVENING independently.

Reporting endpoints are read-only. Export-format generation remains a separate phase and must consume these governed datasets rather than recompute farm authority independently.
