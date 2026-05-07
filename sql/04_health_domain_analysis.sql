-- Deep dive into health deprivation domain of IMD25

WITH health_ranked AS (
    SELECT
        lad_code,
        lad_name,
        imd_avg_score,
        health_avg_score,
        health_avg_rank,
        health_pct_most_deprived,
        imd_pct_most_deprived,
        RANK() OVER (ORDER BY health_avg_score DESC) AS health_deprivation_rank,
        RANK() OVER (ORDER BY imd_avg_score DESC)    AS overall_deprivation_rank,
        NTILE(4) OVER (ORDER BY health_avg_score DESC) AS health_quartile
    FROM dbo.imd25_lad_summaries
    WHERE health_avg_score IS NOT NULL
),
quartile_summary AS (
    SELECT
        health_quartile,
        COUNT(*)                                AS lad_count,
        ROUND(AVG(health_avg_score), 3)         AS avg_health_score,
        ROUND(AVG(imd_avg_score), 2)            AS avg_imd_score,
        ROUND(AVG(health_pct_most_deprived), 3) AS avg_pct_health_deprived,
        MIN(lad_name)                           AS example_most_deprived_lad
    FROM health_ranked
    GROUP BY health_quartile
),
rank_divergence AS (
    SELECT
        lad_name,
        overall_deprivation_rank,
        health_deprivation_rank,
        health_deprivation_rank - overall_deprivation_rank AS rank_divergence,
        health_avg_score,
        imd_avg_score,
        health_pct_most_deprived
    FROM health_ranked
)
SELECT
    h.lad_name,
    h.health_deprivation_rank,
    h.overall_deprivation_rank,
    h.rank_divergence,
    CASE
        WHEN h.rank_divergence <= -20 THEN 'Health worse than overall'
        WHEN h.rank_divergence >= 20  THEN 'Health better than overall'
        ELSE 'Broadly aligned'
    END AS divergence_category,
    h.health_avg_score,
    h.imd_avg_score,
    h.health_pct_most_deprived,
    q.avg_health_score AS quartile_avg_health_score
FROM rank_divergence h
JOIN quartile_summary q
    ON q.health_quartile = (
        SELECT health_quartile FROM health_ranked WHERE lad_code = (
            SELECT lad_code FROM health_ranked hr WHERE hr.lad_name = h.lad_name
        )
    )
ORDER BY h.health_deprivation_rank;
