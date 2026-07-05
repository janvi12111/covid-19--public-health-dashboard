"""
COVID-19 Public Health Dashboard — analysis & chart generation.

Reads the cleaned CSVs from data/processed and produces the portfolio
charts (trend lines, 7/14-day moving averages, top-10 countries bar chart,
week-over-week growth heatmap, vaccination vs. mortality correlation).

Every chart is written to python/images/ as PNG automatically.

Usage
-----
    python python/analysis.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


PROCESSED = Path("data/processed")
IMAGES = Path("python/images")
IMAGES.mkdir(parents=True, exist_ok=True)

FEATURED = [
    "United States", "India", "Brazil", "United Kingdom",
    "France", "Germany", "Italy", "Spain",
]

sns.set_theme(style="whitegrid", context="talk")


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    countries = pd.read_csv(PROCESSED / "countries.csv")
    daily = pd.read_csv(PROCESSED / "daily_stats.csv", parse_dates=["date"])
    return countries, daily


def plot_trend_lines(daily: pd.DataFrame) -> None:
    d = daily[daily["country_name"].isin(FEATURED)]
    fig, ax = plt.subplots(figsize=(14, 7))
    for c, g in d.groupby("country_name"):
        ax.plot(g["date"], g["new_cases_ma7"], label=c, linewidth=2)
    ax.set_title("New COVID-19 Cases — 7-Day Moving Average by Country")
    ax.set_xlabel("Date"); ax.set_ylabel("New cases (7-day MA)")
    ax.legend(ncol=2, fontsize=10)
    fig.tight_layout()
    fig.savefig(IMAGES / "02_python_trend_lines.png", dpi=140)
    plt.close(fig)


def plot_moving_average_overlay(daily: pd.DataFrame) -> None:
    country = "United States"
    d = daily[daily["country_name"] == country].sort_values("date")
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.bar(d["date"], d["new_cases"], color="#c9d6e3", label="Daily new cases")
    ax.plot(d["date"], d["new_cases_ma7"],  color="#1f77b4", lw=2.5, label="7-day MA")
    ax.plot(d["date"], d["new_cases_ma14"], color="#d62728", lw=2.5, label="14-day MA")
    ax.set_title(f"Smoothing the Noise — {country}: Daily Cases vs Moving Averages")
    ax.set_xlabel("Date"); ax.set_ylabel("New cases")
    ax.legend()
    fig.tight_layout()
    fig.savefig(IMAGES / "02_python_moving_average_overlay.png", dpi=140)
    plt.close(fig)


def plot_top10_bar(daily: pd.DataFrame) -> None:
    totals = (
        daily.groupby("country_name")["new_cases"].sum().sort_values(ascending=True).tail(10)
    )
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.barh(totals.index, totals.values, color="#1f77b4")
    ax.set_title("Top 10 Countries by Total Confirmed Cases (First 24 Months)")
    ax.set_xlabel("Total confirmed cases")
    fig.tight_layout()
    fig.savefig(IMAGES / "02_python_top10_countries.png", dpi=140)
    plt.close(fig)


def plot_wow_heatmap(daily: pd.DataFrame) -> None:
    d = daily[daily["country_name"].isin(FEATURED)].copy()
    # Recompute WoW here to be robust to NaNs in the source column.
    d = d.sort_values(["country_name", "date"])
    weekly = d.groupby("country_name")["new_cases"].transform(lambda s: s.rolling(7).sum())
    prev = d.groupby("country_name")["new_cases"].transform(lambda s: s.rolling(7).sum().shift(7))
    d["wow"] = ((weekly - prev) / prev.replace(0, pd.NA)) * 100
    d["month"] = d["date"].dt.to_period("M").astype(str)
    pivot = d.pivot_table(index="country_name", columns="month",
                          values="wow", aggfunc="mean")
    pivot = pivot.astype(float).clip(-100, 200)
    pivot = pivot.dropna(how="all").dropna(axis=1, how="all")
    if pivot.empty:
        return
    fig, ax = plt.subplots(figsize=(16, 6))
    sns.heatmap(pivot, cmap="RdBu_r", center=0, ax=ax,
                cbar_kws={"label": "WoW % growth"})
    ax.set_title("Week-over-Week Case Growth (%) by Country and Month")
    ax.set_xlabel("Month"); ax.set_ylabel("")
    fig.tight_layout()
    fig.savefig(IMAGES / "02_python_wow_growth_heatmap.png", dpi=140)
    plt.close(fig)


def plot_vax_vs_deaths(daily: pd.DataFrame) -> None:
    d = daily.dropna(subset=["total_vaccinations_per_hundred"]).copy()
    if d.empty:
        return
    # For each country, take avg vax coverage in 2021Q3 vs avg new_deaths_ma7 in 2021Q4+.
    early = d[(d["date"] >= "2021-07-01") & (d["date"] <= "2021-09-30")]
    later = d[(d["date"] >= "2021-10-01")]
    vax = early.groupby("country_name")["total_vaccinations_per_hundred"].mean()
    mort = later.groupby("country_name")["new_deaths_ma7"].mean()
    m = pd.concat([vax, mort], axis=1).dropna()
    m.columns = ["Vax per 100 (Q3-2021)", "Avg daily deaths (Q4+ 2021)"]

    fig, ax = plt.subplots(figsize=(11, 7))
    ax.scatter(m.iloc[:, 0], m.iloc[:, 1], s=80, color="#1f77b4")
    for name, row in m.iterrows():
        ax.annotate(name, (row.iloc[0], row.iloc[1]), fontsize=9, alpha=0.75)
    ax.set_xlabel(m.columns[0]); ax.set_ylabel(m.columns[1])
    ax.set_title("Vaccination Coverage vs Later Mortality")
    fig.tight_layout()
    fig.savefig(IMAGES / "02_python_vax_vs_mortality.png", dpi=140)
    plt.close(fig)


def print_key_findings(daily: pd.DataFrame) -> None:
    print("\n=== Key findings ===")
    peaks = (
        daily.sort_values("new_cases_ma7", ascending=False)
        .groupby("country_name").head(1)[["country_name", "date", "new_cases_ma7"]]
        .sort_values("new_cases_ma7", ascending=False).head(5)
    )
    print("Top 5 peak 7-day MA days:")
    print(peaks.to_string(index=False))

    cfr = (
        daily.groupby("country_name")
        .agg(total_cases=("total_cases", "max"), total_deaths=("total_deaths", "max"))
    )
    cfr["cfr_pct"] = (cfr["total_deaths"] / cfr["total_cases"]) * 100
    print("\nHighest case-fatality rate:")
    print(cfr.sort_values("cfr_pct", ascending=False).head(5).round(2).to_string())


def main() -> None:
    _, daily = load()
    plot_trend_lines(daily)
    plot_moving_average_overlay(daily)
    plot_top10_bar(daily)
    plot_wow_heatmap(daily)
    plot_vax_vs_deaths(daily)
    print_key_findings(daily)
    print(f"\nCharts saved to {IMAGES}/")


if __name__ == "__main__":
    main()
