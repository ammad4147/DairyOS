# DairyOS Calculation Register

## Official monthly COP

`COP/L = Feed Cost/L + OPEX/L`

The official monthly record is `COMLRecord`. Its per-litre values are stored
as `NUMERIC(18,6)` and are never derived from binary floating point. Manual
COP accepts only the three values above; milk volume is an Auto-mode input,
not a manual COP component.

### Golden vectors

| Feed Cost/L | OPEX/L | COP/L |
| ---: | ---: | ---: |
| 125.125000 | 74.875000 | 200.000000 |
| 0.333333 | 0.666667 | 1.000000 |

## Money and rates

PKR amounts are stored as `NUMERIC(18,2)` and governed unit/per-litre rates
as `NUMERIC(18,6)`. Display formatting must not become the calculation
authority.
