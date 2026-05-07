-- HLE trends by deprivation decile showing widening inequality over time

WITH hle_trend AS (
    SELECT
        period,
        period_start,
        sex,
        imd_decile,
        deprivation_label,
        hle,
        hle_pct,
        LAG(hle) OVER (
            PARTITION BY sex, imd_decile
            ORDER BY period_start
        ) AS hle_prev_period,
        RANK() OVER (PARTITION BY sex, imd_decile ORDER BY period_start) AS period_rank
    FROM dbo.le_hle_by_deprivation
),
change AS (
    SELECT
        period,
        period_start,
        sex,
        imd_decile,
        deprivation_label,
        hle,
        hle_pct,
        ROUND(hle - hle_prev_period, 2) AS hle_change_from_prev,
        period_rank
    FROM hle_trend
),
gap_trend AS (
    SELECT
        c.period,
        c.period_start,
        c.sex,
        c.imd_decile,
        c.deprivation_label,
        c.hle,
        c.hle_pct,
        c.hle_change_from_prev,
        MAX(CASE WHEN c2.imd_decile = 10 THEN c2.hle END) OVER (
            PARTITION BY c.period, c.sex
        ) - MAX(CASE WHEN c2.imd_decile = 1 THEN c2.hle END) OVER (
            PARTITION BY c.period, c.sex
        ) AS hle_gap_decile_1_to_10
    FROM change c
    JOIN change c2
        ON c.period = c2.period AND c.sex = c2.sex
)
SELECT DISTINCT
    period,
    period_start,
    sex,
    imd_decile,
    deprivation_label,
    hle,
    hle_pct,
    hle_change_from_prev,
    ROUND(hle_gap_decile_1_to_10, 1) AS hle_inequality_gap
FROM gap_trend
ORDER BY sex, period_start, imd_decile;
