# Power BI Dashboard — Build Guide

The Python step already produces `data/processed/powerbi_daily_enriched.csv`
with 7/14-day moving averages, WoW growth, and CFR pre-computed, so Power BI
just visualises — no heavy modelling required.

## 1. Data model

Import both files from `data/processed/`:

- **countries.csv** — dimension. Mark `country_id` as the key.
- **powerbi_daily_enriched.csv** — fact. Grain: one row per country per day.

Create a relationship:
`countries[country_id] 1 ── * powerbi_daily_enriched[country_id]`
(single direction, single-select).

Add a **Date table** (Modeling → New Table):

```DAX
DateTable =
CALENDAR ( DATE(2020,1,22), DATE(2022,1,22) )
```

Mark it as a date table and relate `DateTable[Date] 1 ── * powerbi_daily_enriched[date]`.

## 2. KPI card DAX measures

```DAX
Total Confirmed Cases =
CALCULATE ( MAX ( 'powerbi_daily_enriched'[total_cases] ),
            LASTDATE ( 'DateTable'[Date] ) )

Total Deaths =
CALCULATE ( MAX ( 'powerbi_daily_enriched'[total_deaths] ),
            LASTDATE ( 'DateTable'[Date] ) )

Global CFR % =
DIVIDE ( [Total Deaths], [Total Confirmed Cases] ) * 100

Active Cases =
[Total Confirmed Cases] - [Total Deaths]           -- proxy (recovered not in OWID)

7-Day Avg New Cases =
AVERAGEX (
    DATESINPERIOD ( 'DateTable'[Date], MAX ( 'DateTable'[Date] ), -7, DAY ),
    CALCULATE ( SUM ( 'powerbi_daily_enriched'[new_cases] ) )
)

WoW Growth % =
VAR CurWk = CALCULATE (
    SUM ( 'powerbi_daily_enriched'[new_cases] ),
    DATESINPERIOD ( 'DateTable'[Date], MAX ( 'DateTable'[Date] ), -7, DAY )
)
VAR PrevWk = CALCULATE (
    SUM ( 'powerbi_daily_enriched'[new_cases] ),
    DATESINPERIOD ( 'DateTable'[Date], MAX ( 'DateTable'[Date] ) - 7, -7, DAY )
)
RETURN DIVIDE ( CurWk - PrevWk, PrevWk ) * 100
```

## 3. Visuals

| Visual | Field wells |
| --- | --- |
| Filled map | Location = `countries[country_name]`; Size = `[Total Confirmed Cases]` |
| Line chart — daily + MA | Axis = date; Values = SUM(new_cases) as bars, `[7-Day Avg New Cases]` as line overlay |
| Country comparison line | Axis = date; Values = SUM(new_cases); Legend = country_name; filter to 4-8 countries |
| Ranked bar / table | Rows = country_name; Values = `[Total Confirmed Cases]`, `[Global CFR %]`; sort desc |
| KPI card row | The six measures above |

Add a **Date range slicer** on `DateTable[Date]` (between mode) and a
**country multi-select slicer** on `countries[country_name]`.

Optional: drop a **Play Axis** custom visual with `DateTable[Date]` for the
animated "spread over time" story.

## 4. Layout wireframe

```
┌───────────────────────────────────────────────────────────────────┐
│  COVID-19 PUBLIC HEALTH DASHBOARD                                 │
├───────────────────────────────────────────────────────────────────┤
│  [Total Cases] [Total Deaths] [CFR%] [Active] [7d Avg] [WoW%]     │
├───────────────────────────────┬───────────────────────────────────┤
│                               │                                   │
│      Filled map (cases        │      New cases + 7-day MA         │
│      by country)              │      (bar + line overlay)         │
│                               │                                   │
├───────────────────────────────┼───────────────────────────────────┤
│  Country comparison           │  Top 10 table                     │
│  (multi-line, small           │  (cases / deaths per capita /     │
│   multiples optional)         │   fastest-growing 30d)            │
├───────────────────────────────┴───────────────────────────────────┤
│  Date range slicer  |  Country multi-select slicer                │
└───────────────────────────────────────────────────────────────────┘
```

## 5. Screenshots to capture

After building, export these PNGs into the repo `images/` folder:

- `03_powerbi_dashboard_overview.png` — full page 1
- `03_powerbi_map_view.png` — map visual close-up
- `03_powerbi_trend_view.png` — new-cases + MA overlay
- `03_powerbi_country_compare.png` — multi-line comparison
