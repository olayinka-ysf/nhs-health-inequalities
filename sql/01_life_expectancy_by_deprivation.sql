-- Life expectancy gap between most and least deprived deciles over time

WITH decile_extremes AS (
    SELECT
        period,
        period_start,
        sex,
        imd_decile,
        le,
        hle,
        unhealthy_years
    FROM dbo.le_hle_by_deprivation
    WHERE imd_decile IN (1, 10)
),
pivoted AS (
    SELECT
        period,
        period_start,
        sex,
        MAX(CASE WHEN imd_decile = 10 THEN le END) AS le_least_deprived,
        MAX(CASE WHEN imd_decile = 1  THEN le END) AS le_most_deprived,
        MAX(CASE WHEN imd_decile = 10 THEN hle END) AS hle_least_deprived,
        MAX(CASE WHEN imd_decile = 1  THEN hle END) AS hle_most_deprived
    FROM decile_extremes
    GROUP BY period, period_start, sex
),
gaps AS (
    SELECT
        period,
        period_start,
        sex,
        le_least_deprived,
        le_most_deprived,
        ROUND(le_least_deprived - le_most_deprived, 1) AS le_gap_years,
        hle_least_deprived,
        hle_most_deprived,
        ROUND(hle_least_deprived - hle_most_deprived, 1) AS hle_gap_years
    FROM pivoted
)
SELECT *
FROM gaps
ORDER BY sex, period_start;
