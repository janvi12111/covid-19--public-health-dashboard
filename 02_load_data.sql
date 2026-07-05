-- 02_load_data.sql
-- Loads the Python-cleaned CSVs into the schema from 01_schema.sql.
-- PostgreSQL syntax (uses \copy from psql). For SQL Server use BULK INSERT;
-- for SQLite use `.mode csv` + `.import`.
--
-- NOTE: If your source is JHU (wide format), unpivot to long BEFORE loading —
-- the Python step (python/clean_data.py) already produces long-format CSVs.

\copy countries(country_id, country_name, region, population) \
  FROM 'data/processed/countries.csv' WITH (FORMAT csv, HEADER true);

-- daily_stats.csv columns (from clean_data.py):
--   country_name, continent, date, population,
--   total_cases, new_cases, total_deaths, new_deaths,
--   people_vaccinated, people_fully_vaccinated,
--   total_vaccinations_per_hundred, stringency_index,
--   new_cases_ma7, new_cases_ma14, new_deaths_ma7,
--   wow_growth_pct, cfr_pct, country_id
--
-- Load into a staging table, then insert the columns the fact table uses.

CREATE TEMP TABLE stg_daily (
    country_name                     TEXT,
    continent                        TEXT,
    date                             DATE,
    population                       BIGINT,
    total_cases                      BIGINT,
    new_cases                        INTEGER,
    total_deaths                     BIGINT,
    new_deaths                       INTEGER,
    people_vaccinated                BIGINT,
    people_fully_vaccinated          BIGINT,
    total_vaccinations_per_hundred   NUMERIC(6,2),
    stringency_index                 NUMERIC(5,2),
    new_cases_ma7                    NUMERIC,
    new_cases_ma14                   NUMERIC,
    new_deaths_ma7                   NUMERIC,
    wow_growth_pct                   NUMERIC,
    cfr_pct                          NUMERIC,
    country_id                       INTEGER
);

\copy stg_daily FROM 'data/processed/daily_stats.csv' WITH (FORMAT csv, HEADER true);

INSERT INTO daily_stats (
    date, country_id, confirmed_cases, deaths, recovered, active_cases,
    new_cases, new_deaths,
    people_vaccinated, people_fully_vaccinated,
    total_vax_per_hundred, stringency_index
)
SELECT
    date, country_id, total_cases, total_deaths, NULL,
    (total_cases - total_deaths),
    new_cases, new_deaths,
    people_vaccinated, people_fully_vaccinated,
    total_vaccinations_per_hundred, stringency_index
FROM stg_daily
WHERE country_id IS NOT NULL;
