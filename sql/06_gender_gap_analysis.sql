-- Male vs female life expectancy and HLE differences across deprivation deciles

WITH gender_pivot AS (
    SELECT
        period,
        period_start,
        imd_decile,
        deprivation_label,
        MAX(CASE WHEN sex = 'Male'   THEN le  END) AS le_male,
        MAX(CASE WHEN sex = 'Female' THEN le  END) AS le_female,
        MAX(CASE WHEN sex = 'Male'   THEN hle END) AS hle_male,
        MAX(CASE WHEN sex = 'Female' THEN hle END) AS hle_female,
        MAX(CASE WHEN sex = 'Male'   THEN hle_pct END) AS hle_pct_male,
        MAX(CASE WHEN sex = 'Female' THEN hle_pct END) AS hle_pct_female,
        MAX(CASE WHEN sex = 'Male'   THEN unhealthy_years END) AS unhealthy_yrs_male,
        MAX(CASE WHEN sex = 'Female' THEN unhealthy_years END) AS unhealthy_yrs_female
    FROM dbo.le_hle_by_deprivation
    GROUP BY period, period_start, imd_decile, deprivation_label
),
gender_gaps AS (
    SELECT
        period,
        period_start,
        imd_decile,
        deprivation_label,
        le_male,
        le_female,
        ROUND(le_female - le_male, 2)   AS le_gender_gap,
        hle_male,
        hle_female,
        ROUND(hle_female - hle_male, 2) AS hle_gender_gap,
        hle_pct_male,
        hle_pct_female,
        unhealthy_yrs_male,
        unhealthy_yrs_female,
        LAG(ROUND(le_female - le_male, 2)) OVER (
            PARTITION BY imd_decile ORDER BY period_start
        ) AS le_gender_gap_prev,
        RANK() OVER (PARTITION BY period ORDER BY ROUND(le_female - le_male, 2) DESC) AS decile_gender_gap_rank
    FROM gender_pivot
)
SELECT
    period,
    period_start,
    imd_decile,
    deprivation_label,
    le_male,
    le_female,
    le_gender_gap,
    hle_male,
    hle_female,
    hle_gender_gap,
    hle_pct_male,
    hle_pct_female,
    unhealthy_yrs_male,
    unhealthy_yrs_female,
    ROUND(le_gender_gap - COALESCE(le_gender_gap_prev, le_gender_gap), 2) AS gender_gap_change,
    decile_gender_gap_rank
FROM gender_gaps
ORDER BY period_start, imd_decile;
