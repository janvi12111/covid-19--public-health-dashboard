"""
COVID-19 Public Health Dashboard — data cleaning.

Reads the raw OWID COVID-19 dataset, scopes it to the first 24 months of the
pandemic and the top 30 countries by cumulative cases, standardises country
names, handles missing values, and writes cleaned CSVs for the SQL and
Power BI layers to consume.

Usage
-----
    python python/clean_data.py \
        --input data/raw/owid-covid-data.csv \
        --outdir data/processed
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


COUNTRY_NAME_FIXES = {
    "United States": "United States",
    "US": "United States",
    "USA": "United States",
    "Russia": "Russian Federation",
    "South Korea": "Korea, South",
    "Korea, Republic of": "Korea, South",
    "Iran": "Iran, Islamic Republic of",
    "Vietnam": "Viet Nam",
    "Czechia": "Czech Republic",
    "United Kingdom": "United Kingdom",
    "Bolivia": "Bolivia (Plurinational State of)",
}

START_DATE = "2020-01-22"   # first JHU/OWID reporting day
END_DATE = "2022-01-22"     # first 24 months
TOP_N = 30


def load_raw(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    # OWID mixes country rows with aggregate rows (World, continents, income
    # groups). Aggregates have no iso_code or an OWID_* iso_code — drop them.
    df = df[df["iso_code"].notna() & ~df["iso_code"].str.startswith("OWID_")]
    df["date"] = pd.to_datetime(df["date"])
    return df


def scope(df: pd.DataFrame) -> pd.DataFrame:
    df = df[(df["date"] >= START_DATE) & (df["date"] <= END_DATE)].copy()
    totals = (
        df.groupby("location")["total_cases"].max().sort_values(ascending=False)
    )
    top_countries = totals.head(TOP_N).index.tolist()
    df = df[df["location"].isin(top_countries)].copy()
    df["location"] = df["location"].replace(COUNTRY_NAME_FIXES)
    return df


def build_daily_stats(df: pd.DataFrame) -> pd.DataFrame:
    keep = [
        "location", "continent", "date", "population",
        "total_cases", "new_cases", "total_deaths", "new_deaths",
        "people_vaccinated", "people_fully_vaccinated",
        "total_vaccinations_per_hundred", "stringency_index",
    ]
    out = df[keep].copy()
    for col in ["new_cases", "new_deaths"]:
        out[col] = out[col].fillna(0).clip(lower=0)
    out = out.sort_values(["location", "date"])

    # Derived: 7d / 14d moving averages, WoW growth, active-cases proxy, CFR
    grp = out.groupby("location", group_keys=False)
    out["new_cases_ma7"]  = grp["new_cases"].transform(lambda s: s.rolling(7).mean())
    out["new_cases_ma14"] = grp["new_cases"].transform(lambda s: s.rolling(14).mean())
    out["new_deaths_ma7"] = grp["new_deaths"].transform(lambda s: s.rolling(7).mean())

    weekly = grp["new_cases"].transform(lambda s: s.rolling(7).sum())
    prev_weekly = grp["new_cases"].transform(lambda s: s.rolling(7).sum().shift(7))
    out["wow_growth_pct"] = ((weekly - prev_weekly) / prev_weekly.replace(0, pd.NA)) * 100

    out["cfr_pct"] = (out["total_deaths"] / out["total_cases"].replace(0, pd.NA)) * 100
    out = out.rename(columns={"location": "country_name"})
    return out


def build_countries(df: pd.DataFrame) -> pd.DataFrame:
    countries = (
        df.groupby("location")
        .agg(region=("continent", "first"), population=("population", "max"))
        .reset_index()
        .rename(columns={"location": "country_name"})
    )
    countries["country_name"] = countries["country_name"].replace(COUNTRY_NAME_FIXES)
    countries = countries.reset_index(drop=True)
    countries.insert(0, "country_id", countries.index + 1)
    return countries


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",  default="data/raw/owid-covid-sample-30k.csv")
    parser.add_argument("--outdir", default="data/processed")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    raw = load_raw(Path(args.input))
    scoped = scope(raw)

    countries = build_countries(scoped)
    daily = build_daily_stats(scoped)

    daily = daily.merge(
        countries[["country_id", "country_name"]], on="country_name", how="left"
    )

    countries.to_csv(outdir / "countries.csv", index=False)
    daily.to_csv(outdir / "daily_stats.csv", index=False)

    # Power BI-ready pre-aggregated export (already has MAs and growth).
    daily.to_csv(outdir / "powerbi_daily_enriched.csv", index=False)

    print(f"Wrote {len(countries)} countries and {len(daily):,} daily rows to {outdir}")


if __name__ == "__main__":
    main()
