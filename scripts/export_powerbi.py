import pandas as pd
import os

os.makedirs("output", exist_ok=True)


def run():
    le = pd.read_csv("data/processed/le_hle_by_deprivation.csv")
    lad = pd.read_csv("data/processed/la_deprivation_merged.csv")
    imd = pd.read_csv("data/processed/imd25_lad_summaries.csv")

    # flatten for Power BI relationships
    le_pbi = le[[
        "period", "period_start", "period_end", "imd_decile", "deprivation_label",
        "sex", "le", "hle", "hle_pct", "unhealthy_years"
    ]].copy()
    le_pbi.to_csv("output/pbi_deprivation_trends.csv", index=False)
    print(f"  Saved pbi_deprivation_trends.csv: {len(le_pbi):,} rows")

    lad_pbi = lad[[
        "lad_code", "lad_name_le", "sex", "le_value", "period",
        "imd_avg_score", "imd_pct_most_deprived", "imd_extent",
        "health_avg_score", "health_pct_most_deprived", "imd_deprivation_decile"
    ]].copy()
    lad_pbi.to_csv("output/pbi_la_deprivation.csv", index=False)
    print(f"  Saved pbi_la_deprivation.csv: {len(lad_pbi):,} rows")

    imd_pbi = imd[[
        "lad_code", "lad_name", "imd_avg_score", "imd_avg_rank",
        "imd_pct_most_deprived", "imd_extent",
        "health_avg_score", "health_pct_most_deprived"
    ]].copy()
    imd_pbi.to_csv("output/pbi_imd25_lad_summary.csv", index=False)
    print(f"  Saved pbi_imd25_lad_summary.csv: {len(imd_pbi):,} rows")

    print("\nPower BI CSVs saved to output/")


if __name__ == "__main__":
    run()
