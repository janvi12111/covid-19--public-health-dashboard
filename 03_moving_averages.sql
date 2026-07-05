-- 03_moving_averages.sql
-- 7-day and 14-day moving averages of new cases / new deaths, per country.
-- Uses a windowed AVG with a moving frame (6 preceding + current = 7 rows).

SELECT
    c.country_name,
    d.date,
    d.new_cases,
    ROUND(AVG(d.new_cases)  OVER w7,  2) AS new_cases_ma7,
    ROUND(AVG(d.new_cases)  OVER w14, 2) AS new_cases_ma14,
    ROUND(AVG(d.new_deaths) OVER w7,  2) AS new_deaths_ma7
FROM daily_stats d
JOIN countries   c USING (country_id)
WINDOW
    w7  AS (PARTITION BY d.country_id ORDER BY d.date
            ROWS BETWEEN  6 PRECEDING AND CURRENT ROW),
    w14 AS (PARTITION BY d.country_id ORDER BY d.date
            ROWS BETWEEN 13 PRECEDING AND CURRENT ROW)
ORDER BY c.country_name, d.date;
