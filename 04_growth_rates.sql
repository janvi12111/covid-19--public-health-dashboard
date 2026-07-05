-- 04_growth_rates.sql
-- Week-over-week new-case growth per country, using LAG on a weekly aggregate.

WITH weekly AS (
    SELECT
        country_id,
        DATE_TRUNC('week', date)::date AS week_start,
        SUM(new_cases) AS weekly_new_cases
    FROM daily_stats
    GROUP BY country_id, DATE_TRUNC('week', date)
)
SELECT
    c.country_name,
    w.week_start,
    w.weekly_new_cases,
    LAG(w.weekly_new_cases) OVER (PARTITION BY w.country_id ORDER BY w.week_start)
        AS previous_week_cases,
    ROUND(
        100.0 * (w.weekly_new_cases -
                 LAG(w.weekly_new_cases) OVER (PARTITION BY w.country_id ORDER BY w.week_start))
              / NULLIF(LAG(w.weekly_new_cases) OVER (PARTITION BY w.country_id ORDER BY w.week_start), 0),
        2
    ) AS wow_growth_pct
FROM weekly w
JOIN countries c USING (country_id)
ORDER BY c.country_name, w.week_start;
