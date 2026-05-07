-- Regions with highest concentration of deprived local authorities

WITH region_lookup AS (
    SELECT
        lad_code,
        lad_name,
        imd_avg_score,
        imd_pct_most_deprived,
        imd_extent,
        CASE
            WHEN lad_code LIKE 'E06000001' OR lad_code LIKE 'E06000002'
              OR lad_code LIKE 'E06000003' OR lad_code LIKE 'E06000004'
              OR lad_code LIKE 'E06000005' THEN 'North East'
            WHEN lad_code LIKE 'E06000006' OR lad_code LIKE 'E06000007'
              OR lad_code LIKE 'E06000008' OR lad_code LIKE 'E06000009'
              OR lad_code LIKE 'E06000010' OR lad_code LIKE 'E06000011'
              OR lad_code LIKE 'E06000012' OR lad_code LIKE 'E08%' THEN 'North West'
            WHEN lad_code LIKE 'E07%' AND lad_code >= 'E07000163'
              AND lad_code <= 'E07000211' THEN 'Yorkshire and the Humber'
            WHEN lad_code LIKE 'E06000013' OR lad_code LIKE 'E06000014'
              OR lad_code LIKE 'E06000049' OR lad_code LIKE 'E06000050'
              OR (lad_code LIKE 'E07%' AND lad_code >= 'E07000026'
                  AND lad_code <= 'E07000061') THEN 'East Midlands'
            WHEN lad_code LIKE 'E11%' OR lad_code LIKE 'E09%' THEN 'London'
            WHEN lad_code LIKE 'E06000031' OR lad_code LIKE 'E06000032'
              OR lad_code LIKE 'E06000033' THEN 'South West'
            ELSE 'Other England'
        END AS region
    FROM dbo.imd25_lad_summaries
),
region_stats AS (
    SELECT
        region,
        COUNT(*)                                AS lad_count,
        ROUND(AVG(imd_avg_score), 2)            AS avg_imd_score,
        ROUND(AVG(imd_pct_most_deprived), 3)    AS avg_pct_most_deprived,
        ROUND(MAX(imd_avg_score), 2)            AS max_imd_score,
        ROUND(MIN(imd_avg_score), 2)            AS min_imd_score,
        SUM(CASE WHEN imd_pct_most_deprived >= 0.3 THEN 1 ELSE 0 END) AS highly_deprived_lads
    FROM region_lookup
    GROUP BY region
)
SELECT
    region,
    lad_count,
    avg_imd_score,
    avg_pct_most_deprived,
    max_imd_score,
    min_imd_score,
    highly_deprived_lads,
    RANK() OVER (ORDER BY avg_imd_score DESC) AS deprivation_rank
FROM region_stats
ORDER BY avg_imd_score DESC;
