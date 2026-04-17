-- Local authority rankings by health outcomes relative to deprivation

WITH le_latest AS (
    SELECT
        lad_code,
        lad_name_le,
        sex,
        le_value,
        imd_avg_score,
        imd_pct_most_deprived,
        health_avg_score,
        imd_deprivation_decile
    FROM dbo.la_deprivation_merged
    WHERE sex IN ('Male', 'Female')
),
le_wide AS (
    SELECT
        lad_code,
        MAX(lad_name_le)                                      AS lad_name,
        MAX(imd_avg_score)                                    AS imd_avg_score,
        MAX(imd_pct_most_deprived)                            AS imd_pct_most_deprived,
        MAX(health_avg_score)                                 AS health_avg_score,
        MAX(imd_deprivation_decile)                           AS imd_deprivation_decile,
        MAX(CASE WHEN sex = 'Male'   THEN le_value END)       AS le_male,
        MAX(CASE WHEN sex = 'Female' THEN le_value END)       AS le_female
    FROM le_latest
    GROUP BY lad_code
),
ranked AS (
    SELECT
        lad_code,
        lad_name,
        imd_avg_score,
        imd_pct_most_deprived,
        health_avg_score,
        imd_deprivation_decile,
        le_male,
        le_female,
        ROUND((COALESCE(le_male, 0) + COALESCE(le_female, 0)) /
            NULLIF(
                (CASE WHEN le_male IS NOT NULL THEN 1 ELSE 0 END +
                 CASE WHEN le_female IS NOT NULL THEN 1 ELSE 0 END), 0
            ), 2) AS le_avg,
        RANK() OVER (ORDER BY le_male DESC NULLS LAST)   AS le_male_rank,
        RANK() OVER (ORDER BY le_female DESC NULLS LAST) AS le_female_rank,
        RANK() OVER (ORDER BY imd_avg_score ASC)         AS imd_rank_least_deprived
    FROM le_wide
)
SELECT
    r.lad_name,
    r.imd_avg_score,
    r.imd_pct_most_deprived,
    r.health_avg_score,
    r.le_male,
    r.le_female,
    r.le_avg,
    r.le_male_rank,
    r.le_female_rank,
    r.imd_rank_least_deprived,
    r.le_male_rank - r.imd_rank_least_deprived AS outcome_vs_deprivation_gap,
    CASE
        WHEN r.le_male_rank - r.imd_rank_least_deprived < -30 THEN 'Underperforming'
        WHEN r.le_male_rank - r.imd_rank_least_deprived > 30  THEN 'Overperforming'
        ELSE 'Expected'
    END AS performance_category
FROM ranked r
ORDER BY r.le_avg DESC;
