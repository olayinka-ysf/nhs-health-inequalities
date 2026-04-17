import pandas as pd
import numpy as np
import os

RAW = "data/raw"
PROCESSED = "data/processed"
os.makedirs(PROCESSED, exist_ok=True)


# ── Extraction ────────────────────────────────────────────────────────────────

def extract_le_by_deprivation():
    xl = pd.ExcelFile(f"{RAW}/hle_by_deprivation_timeseries.xlsx")
    le = pd.read_excel(xl, sheet_name="1", header=6)
    hle = pd.read_excel(xl, sheet_name="4", header=6)
    sii_le = pd.read_excel(xl, sheet_name="3", header=6)
    sii_hle = pd.read_excel(xl, sheet_name="6", header=6)
    return le, hle, sii_le, sii_hle


def extract_imd25():
    imd_lsoa = pd.read_csv(f"{RAW}/imd25_all_ranks_scores_deciles.csv")
    lad_xl = pd.ExcelFile(f"{RAW}/imd25_lad_summaries.xlsx")
    lad_imd = pd.read_excel(lad_xl, sheet_name="IMD", header=0)
    lad_health = pd.read_excel(lad_xl, sheet_name="Health", header=0)
    return imd_lsoa, lad_imd, lad_health


def extract_le_local_authority():
    df = pd.read_csv(f"{RAW}/le_by_local_authority_timeseries.csv")
    return df


# ── Transformation ────────────────────────────────────────────────────────────

def clean_le_deprivation(le, hle):
    le = le.copy()
    hle = hle.copy()

    le.columns = [
        "period", "imd_decile", "sex", "sex_code",
        "age_group", "age_code", "le", "le_lci", "le_uci"
    ]
    hle.columns = [
        "period", "imd_decile", "sex", "sex_code",
        "age_group", "age_code", "hle", "hle_lci", "hle_uci", "hle_pct"
    ]

    for df in [le, hle]:
        df.dropna(subset=["period", "imd_decile"], inplace=True)
        df["period"] = df["period"].astype(str).str.strip()
        df["imd_decile"] = df["imd_decile"].astype(int)
        df["sex"] = df["sex"].str.strip()
        df["age_group"] = df["age_group"].astype(str).str.strip()
        df["period_start"] = df["period"].str[:4].astype(int)
        df["period_end"] = df["period"].str[-4:].astype(int)

    # filter to at-birth (youngest age group in dataset)
    le_birth = le[le["age_group"] == "<1"].copy()
    hle_birth = hle[hle["age_group"] == "<1"].copy()

    merged = le_birth.merge(
        hle_birth[["period", "imd_decile", "sex", "hle", "hle_lci", "hle_uci", "hle_pct",
                   "period_start", "period_end"]],
        on=["period", "imd_decile", "sex"],
        how="inner"
    )
    merged = merged.drop(columns=["period_start_y", "period_end_y"], errors="ignore")
    merged = merged.rename(columns={"period_start_x": "period_start", "period_end_x": "period_end"})
    merged["unhealthy_years"] = merged["le"] - merged["hle"]
    merged["deprivation_label"] = merged["imd_decile"].apply(
        lambda x: "Most deprived" if x == 1 else ("Least deprived" if x == 10 else f"Decile {x}")
    )
    return merged


def clean_imd_lsoa(imd_lsoa):
    df = imd_lsoa.copy()
    col_map = {
        "LSOA code (2021)": "lsoa_code",
        "LSOA name (2021)": "lsoa_name",
        "Local Authority District code (2024)": "lad_code",
        "Local Authority District name (2024)": "lad_name",
        "Index of Multiple Deprivation (IMD) Score": "imd_score",
        "Index of Multiple Deprivation (IMD) Rank (where 1 is most deprived)": "imd_rank",
        "Index of Multiple Deprivation (IMD) Decile (where 1 is most deprived 10% of LSOAs)": "imd_decile",
        "Income Score (rate)": "income_score",
        "Employment Score (rate)": "employment_score",
        "Education, Skills and Training Score": "education_score",
        "Health Deprivation and Disability Score": "health_score",
        "Crime Score": "crime_score",
        "Barriers to Housing and Services Score": "barriers_score",
        "Living Environment Score": "living_env_score",
        "Total population: mid 2022": "total_population",
    }
    df = df.rename(columns=col_map)
    keep = list(col_map.values())
    df = df[keep].copy()
    df.dropna(subset=["lsoa_code", "imd_score"], inplace=True)
    return df


def clean_lad_imd(lad_imd, lad_health):
    imd = lad_imd.copy()
    health = lad_health.copy()

    imd_clean = pd.DataFrame({
        "lad_code": imd.iloc[:, 0].astype(str).str.strip(),
        "lad_name": imd.iloc[:, 1].astype(str).str.strip(),
        "imd_avg_rank": pd.to_numeric(imd.iloc[:, 2], errors="coerce"),
        "imd_avg_score": pd.to_numeric(imd.iloc[:, 4], errors="coerce"),
        "imd_pct_most_deprived": pd.to_numeric(imd.iloc[:, 6], errors="coerce"),
        "imd_extent": pd.to_numeric(imd.iloc[:, 8], errors="coerce"),
    })

    health_clean = pd.DataFrame({
        "lad_code": health.iloc[:, 0].astype(str).str.strip(),
        "health_avg_rank": pd.to_numeric(health.iloc[:, 2], errors="coerce"),
        "health_avg_score": pd.to_numeric(health.iloc[:, 4], errors="coerce"),
        "health_pct_most_deprived": pd.to_numeric(health.iloc[:, 6], errors="coerce"),
    })

    merged = imd_clean.merge(health_clean, on="lad_code", how="left")
    merged.dropna(subset=["lad_code", "imd_avg_score"], inplace=True)
    return merged


def clean_le_local_authority(le_la):
    df = le_la.copy()
    df = df.drop(columns=["sex"], errors="ignore")
    df = df.rename(columns={
        "v4_2": "le_value",
        "Lower CI": "le_lci",
        "Upper CI": "le_uci",
        "Time": "period",
        "administrative-geography": "lad_code",
        "Geography": "lad_name",
        "Sex": "sex",
        "AgeGroups": "age_group",
    })
    df = df[["le_value", "le_lci", "le_uci", "period", "lad_code", "lad_name", "sex", "age_group"]].copy()
    df.dropna(subset=["le_value", "lad_code"], inplace=True)
    df["period"] = df["period"].astype(str).str.strip()
    df["lad_code"] = df["lad_code"].astype(str).str.strip()
    df["sex"] = df["sex"].str.strip()
    df["age_group"] = df["age_group"].astype(str).str.strip()

    # youngest available age group as proxy for LE at birth
    df_birth = df[df["age_group"] == "01-04"].copy()
    return df_birth, df


def merge_la_deprivation(le_la_birth, lad_summaries):
    # use most recent period available per LA and sex
    latest_period = le_la_birth.groupby(["lad_code", "sex"])["period"].max().reset_index()
    le_latest = le_la_birth.merge(latest_period, on=["lad_code", "sex", "period"])

    merged = le_latest.merge(lad_summaries, on="lad_code", how="inner")
    merged = merged.rename(columns={"lad_name_x": "lad_name_le", "lad_name_y": "lad_name_imd"})
    merged["imd_deprivation_decile"] = pd.qcut(
        merged["imd_avg_score"].rank(method="first"),
        q=10,
        labels=[str(i) for i in range(10, 0, -1)]
    )
    return merged


# ── Load ──────────────────────────────────────────────────────────────────────

def load(df, filename):
    path = f"{PROCESSED}/{filename}"
    df.to_csv(path, index=False)
    print(f"  Saved {filename}: {df.shape[0]:,} rows x {df.shape[1]} cols")


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    print("Extracting raw data...")
    le_raw, hle_raw, sii_le_raw, sii_hle_raw = extract_le_by_deprivation()
    imd_lsoa_raw, lad_imd_raw, lad_health_raw = extract_imd25()
    le_la_raw = extract_le_local_authority()

    print("Transforming...")
    le_deprivation = clean_le_deprivation(le_raw, hle_raw)
    imd_lsoa = clean_imd_lsoa(imd_lsoa_raw)
    lad_summaries = clean_lad_imd(lad_imd_raw, lad_health_raw)
    le_la_birth, le_la_all = clean_le_local_authority(le_la_raw)
    la_deprivation = merge_la_deprivation(le_la_birth, lad_summaries)

    print("Loading to data/processed/...")
    load(le_deprivation, "le_hle_by_deprivation.csv")
    load(imd_lsoa, "imd25_lsoa.csv")
    load(lad_summaries, "imd25_lad_summaries.csv")
    load(le_la_all, "le_by_local_authority.csv")
    load(la_deprivation, "la_deprivation_merged.csv")

    print("\nETL complete.")
    return le_deprivation, imd_lsoa, lad_summaries, le_la_all, la_deprivation


if __name__ == "__main__":
    run()
