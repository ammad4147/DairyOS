# DairyOS Static Monthly COML

## Purpose

COML (Cost of Milk Production per Liter) is an operator-confirmed management figure. It is not a live transaction KPI.

For each calendar month DairyOS stores one official record containing:

- Feed Cost per Liter
- OPEX per Liter
- Total COML per Liter (automatic sum)
- Month / Year
- Notes
- Lock/update timestamps
- User who last locked the record

Historical months remain available for reference.

## API

- `GET /farm/coml?month_start=YYYY-MM-01` — selected month status and record.
- `GET /farm/coml/current` — current calendar month status.
- `GET /farm/coml/history` — historical official records.
- `POST /farm/coml/lock` — create or explicitly update the official record for a selected month.
- `GET /farm/coml/settings` — reminder configuration.
- `PUT /farm/coml/settings` — set reminder day (1–28).

The server rejects any `month_start` that is not the first day of its calendar month.

## Reminder semantics

The default reminder day is the 1st. Until the selected month has an official record, its reminder state is `UPCOMING`, `DUE`, or `OVERDUE`. A locked month reports `LOCKED`.

## Independence

COML does not consume Finance transactions, Feed Inventory balances, Milk production, Milk sales, or live dashboard data. The TMR preparation tool is an independent calculation aid; saving a TMR draft does not update COML.

The operator must explicitly enter and lock Feed Cost/L and OPEX/L for the selected month.

## UI ownership

- `COML.tsx` owns month selection, official values, reminder state, history, and the TMR tool.
- `TMRPreparationTool.tsx` owns only ration preparation calculations and its local draft.
- `FeedTab.tsx` owns feed operational monitoring only.
- Dashboard reads only the official current-month COML API result.
