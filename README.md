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

- <img width="2240" height="840" alt="02_python_wow_growth_heatmap" src="https://github.com/user-attachments/assets/d20c752a-a0b8-4496-9e1c-2f1f29e4aea6" />
 — full page 1
- <img width="1680" height="980" alt="02_python_top10_countries" src="https://github.com/user-attachments/assets/cc652948-7308-4c06-a5c8-43b19f0685de" /> <img width="1540" height="980" alt="02_python_vax_vs_mortality" src="https://github.com/user-attachments/assets/474d6349-db84-4b46-bf5e-f407786905c8" />

 — new-cases + MA overlay
- <img width="1960" height="980" alt="02_python_trend_lines" src="https://github.com/user-attachments/assets/3f87675b-bee4-4705-bb61-043b1c51a411" /> <img width="1960" height="980" alt="02_python_moving_average_overlay" src="https://github.com/user-attachments/assets/115d2a40-0afe-4316-ac4b-f070a3491338" />

 — multi-line comparison
