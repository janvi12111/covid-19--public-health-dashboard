-- 05_cfr_and_rankings.sql
-- Case-fatality rate and top-N leaderboards.

-- (a) Case-fatality rate by country + global.
SELECT
    c.country_name,
    MAX(d.confirmed_cases)                                        AS total_cases,
    MAX(d.deaths)                                                 AS total_deaths,
    ROUND(100.0 * MAX(d.deaths) / NULLIF(MAX(d.confirmed_cases),0), 2) AS cfr_pct
FROM daily_stats d
JOIN countries   c USING (country_id)
GROUP BY c.country_name
ORDER BY cfr_pct DESC;

-- (b) Global CFR.
SELECT
    ROUND(100.0 * SUM(deaths_end) / NULLIF(SUM(cases_end),0), 2) AS global_cfr_pct
FROM (
    SELECT MAX(confirmed_cases) AS cases_end, MAX(deaths) AS deaths_end
    FROM daily_stats
    GROUP BY country_id
) t;

-- (c) Top 10 by total cases.
SELECT c.country_name, MAX(d.confirmed_cases) AS total_cases
FROM daily_stats d JOIN countries c USING (country_id)
GROUP BY c.country_name
ORDER BY total_cases DESC
LIMIT 10;

-- (d) Top 10 by deaths per capita.
SELECT
    c.country_name,
    MAX(d.deaths)                                            AS total_deaths,
    c.population,
    ROUND(1e6 * MAX(d.deaths)::numeric / NULLIF(c.population,0), 2)
        AS deaths_per_million
FROM daily_stats d JOIN countries c USING (country_id)
GROUP BY c.country_name, c.population
ORDER BY deaths_per_million DESC
LIMIT 10;

-- (e) Top 10 fastest-growing new cases in the most recent 30 days.
WITH recent AS (
    SELECT country_id, SUM(new_cases) AS recent_cases
    FROM daily_stats
    WHERE date >= (SELECT MAX(date) - INTERVAL '30 days' FROM daily_stats)
    GROUP BY country_id
),
prior AS (
    SELECT country_id, SUM(new_cases) AS prior_cases
    FROM daily_stats
    WHERE date >= (SELECT MAX(date) - INTERVAL '60 days' FROM daily_stats)
      AND date <  (SELECT MAX(date) - INTERVAL '30 days' FROM daily_stats)
    GROUP BY country_id
)
SELECT
    c.country_name,
    r.recent_cases,
    p.prior_cases,
    ROUND(100.0 * (r.recent_cases - p.prior_cases)
                / NULLIF(p.prior_cases, 0), 2) AS growth_pct_30d
FROM recent r
JOIN prior  p USING (country_id)
JOIN countries c USING (country_id)
ORDER BY growth_pct_30d DESC
LIMIT 10;
