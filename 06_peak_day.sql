-- 06_peak_day.sql
-- The single highest new-cases day per country ("peak day").

WITH ranked AS (
    SELECT
        d.country_id,
        d.date,
        d.new_cases,
        ROW_NUMBER() OVER (PARTITION BY d.country_id ORDER BY d.new_cases DESC) AS rn
    FROM daily_stats d
)
SELECT
    c.country_name,
    r.date       AS peak_date,
    r.new_cases  AS peak_new_cases
FROM ranked r
JOIN countries c USING (country_id)
WHERE r.rn = 1
ORDER BY r.new_cases DESC;
