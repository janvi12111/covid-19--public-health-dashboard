-- 01_schema.sql
-- Star-schema-lite for the COVID-19 Public Health Dashboard.
-- Two tables: `countries` (dimension) and `daily_stats` (fact).
-- Compatible with PostgreSQL and (with minor tweaks) SQL Server / SQLite.

DROP TABLE IF EXISTS daily_stats;
DROP TABLE IF EXISTS countries;

CREATE TABLE countries (
    country_id     INTEGER      PRIMARY KEY,
    country_name   VARCHAR(120) NOT NULL UNIQUE,
    region         VARCHAR(60),                 -- OWID continent
    population     BIGINT
);

CREATE TABLE daily_stats (
    date              DATE     NOT NULL,
    country_id        INTEGER  NOT NULL REFERENCES countries(country_id),
    confirmed_cases   BIGINT,                   -- cumulative total_cases
    deaths            BIGINT,                   -- cumulative total_deaths
    recovered         BIGINT,                   -- NULL in OWID; kept for JHU compatibility
    active_cases      BIGINT,                   -- confirmed - deaths - recovered
    new_cases         INTEGER  NOT NULL DEFAULT 0,
    new_deaths        INTEGER  NOT NULL DEFAULT 0,
    people_vaccinated             BIGINT,
    people_fully_vaccinated       BIGINT,
    total_vax_per_hundred         NUMERIC(6,2),
    stringency_index              NUMERIC(5,2),
    PRIMARY KEY (country_id, date)
);

CREATE INDEX idx_daily_stats_date ON daily_stats(date);
CREATE INDEX idx_daily_stats_country ON daily_stats(country_id);
