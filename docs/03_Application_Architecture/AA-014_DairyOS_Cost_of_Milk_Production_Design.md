# AA-014 — DairyOS Cost of Milk Production Design

**Document ID:** AA-014
**Version:** 1.0
**Status:** Approved Baseline
**Related:** AA-013 §15 (Operator Interface Design), AA-009 (Financial Management)

---

# 1. Purpose

Specifies the Cost of Milk Production section: an **independent analytical
calculator**, deliberately not wired into the rest of DairyOS.

Every value is entered by hand. The section produces a defensible cost per
litre from a farm manager's own figures, and can be checked against a
spreadsheet line by line.

This document exists because AA-013 §15 originally specified an integrated
cost engine dependent on the inventory ledger, purchase records, feeding-group
membership history and the finding entity — none of which exist. That design is
superseded here.

---

# 2. Decisions of Record

Taken 2026-08-13.

| # | Decision | Rationale |
|---|---|---|
| D-COP-1 | The section is **independent**. It reads from and writes to nothing else in DairyOS | It works today rather than after four unbuilt dependencies |
| D-COP-2 | All inputs are **manual**, each carrying a `MANUAL` / `LINKED` source flag | Automation becomes a per-field upgrade instead of a rewrite, and no figure is ever ambiguous about its origin |
| D-COP-3 | **Whole-herd allocation** — every cost of keeping the herd divides into the milk it produced | Youngstock exist to become milkers; their upkeep is a cost of milk. No arguable allocation rules, and the total reconciles to the bank |
| D-COP-4 | Both **cash cost** and **full economic cost** are calculated | Cash says whether the farm is surviving; economic says whether it is actually profitable. The gap is usually large |
| D-COP-5 | Feed is entered as **quantity × rate per ingredient** (simple mode only) | Matches how invoices arrive and needs no ration data. Accepted cost: no cost breakdown by biological stage |
| D-COP-6 | By-product income is **deducted, with gross and net both shown** | Standard dairy costing. Showing both reveals how much viability rests on by-products rather than milk |
| D-COP-7 | A saved period **freezes**, inputs included | Otherwise a late correction silently rewrites what a past month cost |
| D-COP-8 | All arithmetic is **visible and exportable** | A farm manager will check this against a spreadsheet, and an unverifiable cost figure will not be trusted |

## 2.1 Accepted cost of D-COP-5

Simple feed entry cannot produce cost per biological stage, which was the
original motivation for linking TMR formulas to purchases. The output structure
below is designed so a **detailed mode** — per-stage ration × head count × days,
using the seven TMR formulas in AA-013 §8.4 — can be added later without
changing the reported figures or breaking period comparability. It is not in
scope now.

---

# 3. Principles

**Independence.** No other module may read this section's outputs, and this
section may not read theirs. If cost per litre is later wanted on the
dashboard, that is a deliberate future decision, not a side effect.

**Provenance on every field.** Each input shows whether it was typed or pulled.
An automated figure and a typed one must never look identical.

**Coverage is reported.** A cost per litre computed from a third of the input
lines is not a cost per litre. The section states how many lines are populated
and which major groups are empty, per AA-013 §2.1: absence of data must never
render as good news.

**Nothing is inferred.** An empty field is empty. The calculator never
substitutes an industry average, a prior period, or an estimate.

---

# 4. Input Schedule — Period and Herd Basis

Required before any per-litre figure can be produced.

| Field | Unit | Source | Notes |
|---|---|---|---|
| Period start | date | MANUAL | |
| Period end | date | MANUAL | |
| Days in period | days | DERIVED | |
| Milk produced | litres | MANUAL *(linkable)* | Total, including milk fed to calves |
| Milk sold | litres | MANUAL *(linkable)* | |
| Milk fed to calves | litres | MANUAL | Produced but not sold |
| Milk discarded | litres | MANUAL | Withheld, spoiled or rejected |
| Average milking cows | head | MANUAL | Average over the period |
| Average dry cows | head | MANUAL | |
| Average heifers | head | MANUAL | Over 12 months, not yet calved |
| Average calves | head | MANUAL | Under 12 months |
| Total average herd | head | DERIVED | Sum of the four above |
| Milk selling price | Rs/litre | MANUAL | For margin and break-even |

---

# 5. Section A — Feed Cost

Entered as quantity consumed in the period × rate per unit (D-COP-5).

## 5.1 Roughage and fodder

| Item | Unit | Fields |
|---|---|---|
| Green fodder (purchased) | kg | qty, Rs/kg |
| Maize / sorghum silage | kg | qty, Rs/kg |
| Wheat straw (toori) | kg | qty, Rs/kg |
| Hay / dry fodder | kg | qty, Rs/kg |
| Other roughage | kg | qty, Rs/kg |

## 5.2 Own-grown fodder

A farm that grows its own fodder and enters only purchased feed will
dramatically understate its cost. Entered as period totals rather than a rate.

| Item | Unit | Notes |
|---|---|---|
| Seed | Rs | |
| Land preparation / ploughing | Rs | |
| Fertiliser and manure applied | Rs | |
| Irrigation (water, electricity, diesel) | Rs | |
| Pesticide / weedicide | Rs | |
| Harvesting and chopping | Rs | |
| Fodder labour | Rs | |
| Fodder transport | Rs | |
| Fodder land rent | Rs | Or imputed if owned |

## 5.3 Concentrates

| Item | Unit | Fields |
|---|---|---|
| Vanda / compound concentrate | kg | qty, Rs/kg |
| Soybean meal | kg | qty, Rs/kg |
| Cottonseed cake (binola) | kg | qty, Rs/kg |
| Maize / crushed grain | kg | qty, Rs/kg |
| Wheat bran (choker) | kg | qty, Rs/kg |
| Rice polish | kg | qty, Rs/kg |
| Molasses | kg | qty, Rs/kg |

## 5.4 Supplements and additives

| Item | Unit | Fields |
|---|---|---|
| Bypass fat | kg | qty, Rs/kg |
| Mineral mixture | kg | qty, Rs/kg |
| Meetha soda (sodium bicarbonate) | kg | qty, Rs/kg |
| Anionic salts (DCAD) | kg | qty, Rs/kg |
| Toxin binder | kg | qty, Rs/kg |
| Amino acids (lysine / methionine) | kg | qty, Rs/kg |
| Vitamins | kg | qty, Rs/kg |
| Common salt | kg | qty, Rs/kg |

## 5.5 Calf feed

| Item | Unit | Fields |
|---|---|---|
| Calf starter | kg | qty, Rs/kg |
| Milk replacer | kg | qty, Rs/kg |

Milk fed to calves is recorded in §4 as litres and is **not** costed again
here; it is production diverted, not feed purchased.

## 5.6 Feed-related charges

| Item | Unit |
|---|---|
| Feed transport and freight | Rs |
| Milling, grinding and mixing charges | Rs |
| Feed storage and spoilage loss | Rs |
| Feed testing / analysis | Rs |

**Total Feed Cost** = Σ (quantity × rate) + §5.2 + §5.6

---

# 6. Section B — OPEX

All operating expenses other than feed.

## 6.1 Labour

| Item | Unit |
|---|---|
| Permanent staff salaries (milkers, feeders, herdsmen) | Rs |
| Supervisor / manager salary | Rs |
| Casual and seasonal labour | Rs |
| Staff food and accommodation | Rs |
| Bonuses and gratuity | Rs |
| EOBI / social security contributions | Rs |
| Staff medical | Rs |

## 6.2 Veterinary and health

| Item | Unit |
|---|---|
| Veterinarian fees / retainer | Rs |
| Medicines and injectables | Rs |
| Vaccines | Rs |
| Deworming | Rs |
| Mastitis treatment and teat dip | Rs |
| Hoof trimming and care | Rs |
| Laboratory and diagnostic tests | Rs |
| Post-mortem and carcass disposal | Rs |

## 6.3 Breeding

| Item | Unit |
|---|---|
| Semen straws | Rs |
| AI technician fees | Rs |
| Liquid nitrogen | Rs |
| Pregnancy diagnosis | Rs |
| Hormones and synchronisation | Rs |
| Bull purchase / maintenance | Rs |

## 6.4 Utilities and fuel

| Item | Unit |
|---|---|
| Electricity | Rs |
| Diesel — generator | Rs |
| Diesel / petrol — vehicles and tractor | Rs |
| Gas | Rs |
| Water and tubewell running cost | Rs |

## 6.5 Milking and milk handling

| Item | Unit |
|---|---|
| Milking machine consumables (liners, filters, tubes) | Rs |
| Detergents and sanitisers | Rs |
| Teat dip and hygiene chemicals | Rs |
| Chilling and cooling cost | Rs |
| Milk transport to buyer | Rs |
| Milk testing and quality charges | Rs |
| Packaging and containers | Rs |

## 6.6 Housing, bedding and hygiene

| Item | Unit |
|---|---|
| Bedding material (sand, husk, sawdust) | Rs |
| Manure removal and disposal | Rs |
| Fly and pest control | Rs |
| Disinfectants and sprays | Rs |
| Washing water | Rs |

## 6.7 Repairs and maintenance

| Item | Unit |
|---|---|
| Machinery and equipment repairs | Rs |
| Vehicle and tractor repairs | Rs |
| Shed, floor and fencing repairs | Rs |
| Generator servicing | Rs |
| Small tools and spares | Rs |

## 6.8 Administration and overheads

| Item | Unit |
|---|---|
| Land rent or lease | Rs |
| Property and agricultural taxes | Rs |
| Livestock insurance | Rs |
| Asset and vehicle insurance | Rs |
| Office and stationery | Rs |
| Phone, internet and software | Rs |
| Accounting, audit and legal | Rs |
| Bank charges | Rs |
| Security / guard | Rs |
| Marketing and selling expenses | Rs |

## 6.9 Financing

| Item | Unit |
|---|---|
| Loan interest | Rs |
| Lease and instalment payments | Rs |

**Total OPEX** = Σ §6.1 … §6.9

---

# 7. Section C — Non-Cash and Economic Costs

Added to cash cost to produce full economic cost (D-COP-4). Excluded from the
cash figure entirely.

| Item | Unit | Notes |
|---|---|---|
| Depreciation — buildings and sheds | Rs | |
| Depreciation — machinery and equipment | Rs | |
| Depreciation — vehicles | Rs | |
| Herd replacement cost | Rs | Cost of raising or buying a replacement heifer, spread over her productive life, × cows replaced in the period |
| Mortality losses | Rs | Value of animals that died |
| Imputed rent on owned land | Rs | Only if not already in §6.8 |
| Imputed family / owner labour | Rs | Unpaid work that would otherwise be hired |
| Opportunity cost of capital | Rs | Optional |

**Herd replacement is the line most often omitted and most often material.** A
herd that is not replacing itself is consuming its own capital while appearing
profitable.

---

# 8. Section D — By-Product Credits

Deducted from cost; gross and net both reported (D-COP-6).

| Item | Unit |
|---|---|
| Manure / dung sales | Rs |
| Manure used on own fodder land (imputed) | Rs |
| Male calf sales | Rs |
| Cull cow and culled animal sales | Rs |
| Empty bags and sacks | Rs |
| Biogas value | Rs |
| Compost sales | Rs |

---

# 9. Calculation Model

Every formula is displayed on screen beside its result (D-COP-8).

```
Total Feed Cost      = Σ Section A
Total OPEX           = Σ Section B
Total Non-Cash       = Σ Section C
By-Product Credits   = Σ Section D

Cash Cost            = Total Feed Cost + Total OPEX
Economic Cost        = Cash Cost + Total Non-Cash
```

## 9.1 Per-litre figures

```
Cash cost per litre produced      = Cash Cost            ÷ Milk produced
Net cash cost per litre produced  = (Cash Cost − Credits) ÷ Milk produced

Economic cost per litre produced     = Economic Cost            ÷ Milk produced
Net economic cost per litre produced = (Economic Cost − Credits) ÷ Milk produced

Net cost per litre SOLD           = (Economic Cost − Credits) ÷ Milk sold
```

**Cost per litre sold is the figure to compare against your milk price.**
Cost per litre produced is the operational efficiency measure. They differ by
the milk fed to calves and discarded, and quoting the wrong one flatters the
farm.

## 9.2 Supporting figures

```
Feed cost per litre       = Total Feed Cost ÷ Milk produced
OPEX per litre            = Total OPEX      ÷ Milk produced
Feed as % of cash cost    = Total Feed Cost ÷ Cash Cost × 100
Cost per head per day     = Cash Cost ÷ (Total average herd × Days)
Milk per cow per day      = Milk produced ÷ (Average milking cows × Days)

Break-even milk price     = Net economic cost per litre sold
Margin per litre          = Milk selling price − Net economic cost per litre sold
Total margin              = Margin per litre × Milk sold
```

Feed as a percentage of cash cost is the single most useful benchmark on the
screen; dairy operations typically run 55–70%, and a figure far outside that
range usually means an input group is empty rather than that the farm is
unusual.

---

# 10. Outputs

## 10.1 Headline

| Figure | |
|---|---|
| Net economic cost per litre sold | The break-even price |
| Milk selling price | |
| Margin per litre | Green or red |
| Total margin for the period | |

## 10.2 Breakdown

Feed Cost and OPEX as totals, percentages and per-litre figures, with OPEX
expanded by the nine groups in §6. Cash and economic columns side by side so
the non-cash gap is visible.

## 10.3 Coverage statement

Populated input lines against total, and a named list of empty groups. A
period with no labour and no utilities entered is reported as such next to its
cost per litre, not silently.

## 10.4 Export

Full input schedule and every formula, exportable for checking and for the
Records section.

---

# 11. Provenance and the Automation Path

Each input carries a source flag (D-COP-2). All start `MANUAL`.

Two fields are worth linking first, because they are high-volume and require no
interpretation:

| Field | Source when linked |
|---|---|
| Milk produced | Milk production records for the period |
| Milk sold | Milk sales records |

OPEX groups may later offer a **pull from ledger** action per group, using the
existing category totals in `CostOfProductionService`. The pulled figure is
shown as `LINKED` with its category, and remains overridable — an override
reverts the field to `MANUAL` and says so.

**Deliberately not automated:** feed quantities (need the inventory ledger),
depreciation and herd replacement (accounting judgements, not records),
by-product credits (rarely booked). Linking these would manufacture precision
that the underlying data does not support.

---

# 12. What This Section Deliberately Does Not Do

- It does not read from or write to any other DairyOS module (D-COP-1).
- It does not raise findings and does not appear in the dashboard action queue.
- It does not break cost down by biological stage (D-COP-5, §2.1).
- It does not reconcile against the financial ledger. The reconciliation
  finding specified in AA-013 v1.2 §15.5 is **withdrawn** along with the
  integrated design.
- It does not infer, estimate or carry values forward between periods.

---

# 13. Backend Requirements

Small, and independent of everything else.

| Item | Notes |
|---|---|
| `CostPeriod` entity | Period dates, status (`DRAFT` / `FROZEN`), created/updated metadata |
| `CostInput` entity | One row per input line: group, item, quantity, rate, amount, source flag |
| Freeze on save | A frozen period's inputs become immutable (D-COP-7); reopening creates a new revision rather than editing in place |
| Calculation service | Pure function of the inputs — no repository reads |
| Export | Inputs and formulas |
| Seed catalogue | The item list in §5–§8, so a farm starts with the schedule rather than a blank page |

The item catalogue should be **governed vocabulary, extensible per farm** — a
farm with a cost this document has not anticipated must be able to add it,
without that addition breaking period comparability.

---

# 14. Open Items

- **Detailed feed mode** — per-stage ration × head × days, per §2.1. Deferred,
  not rejected.
- **Cost per litre on the dashboard** — currently excluded by D-COP-1. Revisit
  once the section has been used for a few periods.
- **Period comparison** — comparing two frozen periods and explaining the
  movement. Natural next step once several periods exist.
- **Currency and units** — assumed PKR and kg/litres throughout; belongs in
  Settings when that section is built.

---

*End of AA-014.*
