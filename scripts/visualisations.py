import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import numpy as np
import os

os.makedirs("output/charts", exist_ok=True)

NHS_BLUE = "#005EB8"
NHS_DARK_BLUE = "#003087"
NHS_LIGHT_BLUE = "#41B6E6"
NHS_DARK_GREEN = "#006747"
NHS_WARM_YELLOW = "#FAE100"
NHS_RED = "#DA291C"
NHS_PALE_GREY = "#F0F4F5"

DEPRIVATION_PALETTE = [
    "#C00000", "#D94F1E", "#E07820", "#E8A825",
    "#EEC900", "#C5D63D", "#8ABD6E", "#57A87D",
    "#2E8B8B", "#005EB8"
]

plt.rcParams.update({
    "font.family": "Arial",
    "font.size": 10,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.labelsize": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "savefig.bbox": "tight",
})


def load_data():
    le = pd.read_csv("data/processed/le_hle_by_deprivation.csv")
    lad = pd.read_csv("data/processed/la_deprivation_merged.csv")
    imd = pd.read_csv("data/processed/imd25_lad_summaries.csv")
    return le, lad, imd


# ── Chart 1: LE trend by deprivation decile ───────────────────────────────────

def chart_le_trend(le):
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=False)
    fig.suptitle(
        "Life Expectancy at Birth by Deprivation Decile, England 2013-2015 to 2022-2024",
        fontsize=13, fontweight="bold", y=1.01
    )

    for ax, sex in zip(axes, ["Male", "Female"]):
        df = le[le["sex"] == sex].copy()
        for i, decile in enumerate(range(1, 11)):
            d = df[df["imd_decile"] == decile].sort_values("period_start")
            lw = 2.5 if decile in (1, 10) else 1.0
            alpha = 1.0 if decile in (1, 10) else 0.55
            label = f"Decile {decile} ({'most' if decile == 1 else 'least'} deprived)" if decile in (1, 10) else f"Decile {decile}"
            ax.plot(d["period_start"], d["le"], color=DEPRIVATION_PALETTE[i],
                    linewidth=lw, alpha=alpha, label=label, marker="o", markersize=3)

        ax.set_title(sex)
        ax.set_xlabel("Period start year")
        ax.set_ylabel("Life expectancy (years)")
        ax.set_xticks(le["period_start"].unique())
        ax.tick_params(axis="x", rotation=45)
        ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f"))
        ax.set_facecolor(NHS_PALE_GREY)

    handles, labels = axes[0].get_legend_handles_labels()
    key_idx = [0, 9]
    key_handles = [handles[i] for i in key_idx]
    key_labels = [labels[i] for i in key_idx]
    fig.legend(key_handles, key_labels, loc="lower center", ncol=2, fontsize=9,
               frameon=False, bbox_to_anchor=(0.5, -0.06))

    plt.tight_layout()
    plt.savefig("output/charts/line_le_by_deprivation_decile.png")
    plt.close()
    print("  Saved: line_le_by_deprivation_decile.png")


# ── Chart 2: 10-year LE gap bar chart ─────────────────────────────────────────

def chart_le_gap(le):
    df = le[le["period"] == "2022 to 2024"].copy()
    gap_data = []
    for sex in ["Male", "Female"]:
        s = df[df["sex"] == sex]
        le_10 = s[s["imd_decile"] == 10]["le"].values[0]
        le_1 = s[s["imd_decile"] == 1]["le"].values[0]
        hle_10 = s[s["imd_decile"] == 10]["hle"].values[0]
        hle_1 = s[s["imd_decile"] == 1]["hle"].values[0]
        gap_data.append({
            "sex": sex,
            "LE gap (years)": round(le_10 - le_1, 1),
            "HLE gap (years)": round(hle_10 - hle_1, 1),
        })
    gap_df = pd.DataFrame(gap_data).melt(id_vars="sex", var_name="Metric", value_name="Gap (years)")

    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(2)
    width = 0.35
    for i, metric in enumerate(["LE gap (years)", "HLE gap (years)"]):
        vals = gap_df[gap_df["Metric"] == metric]["Gap (years)"].values
        color = NHS_BLUE if "LE" in metric else NHS_RED
        bars = ax.bar(x + i * width, vals, width, label=metric, color=color, alpha=0.88)
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
                    f"{val:.1f}", ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax.set_title(
        "Gap in Life Expectancy Between Most and Least Deprived Deciles\n"
        "England, 2022 to 2024",
        fontweight="bold"
    )
    ax.set_xticks(x + width / 2)
    ax.set_xticklabels(["Male", "Female"])
    ax.set_ylabel("Gap (years)")
    ax.set_ylim(0, max(gap_df["Gap (years)"]) + 3)
    ax.legend(frameon=False)
    ax.set_facecolor(NHS_PALE_GREY)
    plt.tight_layout()
    plt.savefig("output/charts/bar_le_gap_most_least_deprived.png")
    plt.close()
    print("  Saved: bar_le_gap_most_least_deprived.png")


# ── Chart 3: Heatmap of health deprivation score by IMD score band ────────────

def chart_heatmap(imd):
    df = imd.copy().dropna(subset=["imd_avg_score", "health_avg_score"])
    df["imd_score_band"] = pd.cut(
        df["imd_avg_score"], bins=10,
        labels=[f"Band {i}" for i in range(1, 11)]
    )
    pivot = df.pivot_table(
        index="imd_score_band",
        values="health_avg_score",
        aggfunc="mean"
    ).sort_index(ascending=False)

    fig, ax = plt.subplots(figsize=(4, 8))
    sns.heatmap(
        pivot, annot=True, fmt=".2f", cmap="RdYlGn_r",
        linewidths=0.5, ax=ax, cbar_kws={"label": "Avg health deprivation score"},
        annot_kws={"size": 9}
    )
    ax.set_title(
        "Average Health Deprivation Score\nby IMD Score Band, England 2025",
        fontweight="bold"
    )
    ax.set_xlabel("Health deprivation score (mean)")
    ax.set_ylabel("IMD score band (Band 10 = most deprived)")
    plt.tight_layout()
    plt.savefig("output/charts/heatmap_health_deprivation_by_imd_band.png")
    plt.close()
    print("  Saved: heatmap_health_deprivation_by_imd_band.png")


# ── Chart 4: Scatter - IMD score vs LE by local authority ─────────────────────

def chart_scatter(lad):
    df = lad[lad["sex"] == "Male"].copy()
    df = df.dropna(subset=["imd_avg_score", "le_value"])

    fig, ax = plt.subplots(figsize=(10, 6))
    sc = ax.scatter(
        df["imd_avg_score"], df["le_value"],
        c=df["imd_avg_score"], cmap="RdYlGn_r",
        alpha=0.65, s=40, linewidths=0
    )
    plt.colorbar(sc, ax=ax, label="IMD average score")

    z = np.polyfit(df["imd_avg_score"].dropna(), df["le_value"].dropna(), 1)
    p = np.poly1d(z)
    x_line = np.linspace(df["imd_avg_score"].min(), df["imd_avg_score"].max(), 100)
    ax.plot(x_line, p(x_line), color=NHS_DARK_BLUE, linewidth=1.5,
            linestyle="--", label="Trend line")

    ax.set_title(
        "IMD Score vs Male Life Expectancy by Local Authority\nEngland",
        fontweight="bold"
    )
    ax.set_xlabel("IMD average score (higher = more deprived)")
    ax.set_ylabel("Life expectancy at birth (years)")
    ax.legend(frameon=False)
    ax.set_facecolor(NHS_PALE_GREY)
    plt.tight_layout()
    plt.savefig("output/charts/scatter_imd_vs_le_local_authority.png")
    plt.close()
    print("  Saved: scatter_imd_vs_le_local_authority.png")


# ── Chart 5: Grouped bar - male vs female HLE by deprivation decile ───────────

def chart_gender_hle(le):
    df = le[le["period"] == "2022 to 2024"].copy()
    decile_labels = [f"D{i}" for i in range(1, 11)]
    x = np.arange(10)
    width = 0.38

    male_hle = df[df["sex"] == "Male"].sort_values("imd_decile")["hle"].values
    female_hle = df[df["sex"] == "Female"].sort_values("imd_decile")["hle"].values

    fig, ax = plt.subplots(figsize=(12, 6))
    bars_m = ax.bar(x - width / 2, male_hle, width, label="Male", color=NHS_BLUE, alpha=0.88)
    bars_f = ax.bar(x + width / 2, female_hle, width, label="Female", color=NHS_RED, alpha=0.75)

    ax.set_title(
        "Healthy Life Expectancy at Birth by Sex and Deprivation Decile\n"
        "England, 2022 to 2024 (Decile 1 = most deprived)",
        fontweight="bold"
    )
    ax.set_xlabel("IMD deprivation decile")
    ax.set_ylabel("Healthy life expectancy (years)")
    ax.set_xticks(x)
    ax.set_xticklabels(decile_labels)
    ax.legend(frameon=False)
    ax.set_ylim(0, max(female_hle.max(), male_hle.max()) + 8)
    ax.set_facecolor(NHS_PALE_GREY)

    for bar in bars_m:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                f"{bar.get_height():.0f}", ha="center", va="bottom", fontsize=7.5)
    for bar in bars_f:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                f"{bar.get_height():.0f}", ha="center", va="bottom", fontsize=7.5)

    plt.tight_layout()
    plt.savefig("output/charts/bar_gender_hle_by_deprivation_decile.png")
    plt.close()
    print("  Saved: bar_gender_hle_by_deprivation_decile.png")


if __name__ == "__main__":
    print("Loading data...")
    le, lad, imd = load_data()
    print("Generating charts...")
    chart_le_trend(le)
    chart_le_gap(le)
    chart_heatmap(imd)
    chart_scatter(lad)
    chart_gender_hle(le)
    print("\nAll charts saved to output/charts/")
