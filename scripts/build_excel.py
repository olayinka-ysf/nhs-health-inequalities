import pandas as pd
import xlsxwriter
import os

os.makedirs("output/excel", exist_ok=True)

NHS_BLUE = "#005EB8"
NHS_DARK_BLUE = "#003087"
NHS_WHITE = "#FFFFFF"
NHS_PALE_GREY = "#F0F4F5"
NHS_LIGHT_BLUE = "#41B6E6"
NHS_RED = "#DA291C"
NHS_DARK_GREEN = "#006747"

OUTPUT = "output/excel/nhs_health_inequalities_analysis.xlsx"


def load_data():
    le = pd.read_csv("data/processed/le_hle_by_deprivation.csv")
    lad = pd.read_csv("data/processed/la_deprivation_merged.csv")
    imd = pd.read_csv("data/processed/imd25_lad_summaries.csv")
    return le, lad, imd


def add_header(ws, workbook, title, subtitle=None):
    header_fmt = workbook.add_format({
        "bold": True, "font_size": 14, "font_color": NHS_WHITE,
        "bg_color": NHS_DARK_BLUE, "valign": "vcenter", "align": "left",
        "left": 1, "right": 1, "top": 1, "bottom": 1,
    })
    sub_fmt = workbook.add_format({
        "italic": True, "font_size": 10, "font_color": "#444444",
        "bg_color": NHS_PALE_GREY, "align": "left",
        "left": 1, "right": 1, "bottom": 1,
    })
    ws.merge_range("A1:H1", title, header_fmt)
    ws.set_row(0, 28)
    if subtitle:
        ws.merge_range("A2:H2", subtitle, sub_fmt)
        ws.set_row(1, 18)
    return 3 if subtitle else 2


def col_header_fmt(workbook):
    return workbook.add_format({
        "bold": True, "font_color": NHS_WHITE, "bg_color": NHS_BLUE,
        "border": 1, "align": "center", "valign": "vcenter",
        "text_wrap": True,
    })


def data_fmt(workbook, number_format=None, bg=None):
    fmt = {
        "border": 1, "valign": "vcenter",
        "bg_color": bg if bg else NHS_WHITE,
    }
    if number_format:
        fmt["num_format"] = number_format
    return workbook.add_format(fmt)


def build_summary(workbook, le):
    ws = workbook.add_worksheet("Summary")
    ws.set_column("A:A", 38)
    ws.set_column("B:C", 16)
    ws.set_column("D:H", 12)

    row = add_header(ws, workbook, "Key Inequality Metrics",
                     "England, 2022 to 2024 | Source: ONS, IMD 2025")

    metric_hdr = workbook.add_format({
        "bold": True, "bg_color": NHS_LIGHT_BLUE, "font_color": NHS_DARK_BLUE,
        "border": 1, "align": "left",
    })
    val_fmt = workbook.add_format({"border": 1, "align": "center", "bold": True, "font_size": 12})
    val_red = workbook.add_format({"border": 1, "align": "center", "bold": True,
                                   "font_size": 12, "font_color": NHS_RED})
    label_fmt = workbook.add_format({"border": 1, "align": "left", "italic": True})

    metrics = [
        ("Male life expectancy gap (most vs least deprived)", "10.4 years", False),
        ("Female life expectancy gap (most vs least deprived)", "8.1 years", False),
        ("Male healthy life expectancy gap (most vs least deprived)", "19.4 years", True),
        ("Female healthy life expectancy gap (most vs least deprived)", "20.3 years", True),
        ("Most deprived male LE at birth (Decile 1)", "73.2 years", False),
        ("Least deprived male LE at birth (Decile 10)", "83.6 years", False),
        ("Most deprived female HLE at birth (Decile 1)", "48.2 years", True),
        ("Least deprived female HLE at birth (Decile 10)", "68.5 years", True),
    ]

    ws.write(row, 0, "Metric", metric_hdr)
    ws.write(row, 1, "Value (2022-2024)", metric_hdr)
    ws.write(row, 2, "Category", metric_hdr)
    row += 1

    for metric, val, is_hle in metrics:
        ws.write(row, 0, metric, label_fmt)
        ws.write(row, 1, val, val_red if "gap" in metric.lower() else val_fmt)
        ws.write(row, 2, "HLE" if is_hle else "Life Expectancy", label_fmt)
        ws.set_row(row, 20)
        row += 1

    row += 1
    note_fmt = workbook.add_format({"italic": True, "font_color": "#666666", "align": "left"})
    ws.merge_range(row, 0, row, 4,
                   "Note: IMD decile 1 = most deprived 10% of areas; decile 10 = least deprived 10%.",
                   note_fmt)

    ws.activate()
    print("  Built: Summary sheet")


def build_deprivation_trends(workbook, le):
    ws = workbook.add_worksheet("Deprivation Trends")
    ws.set_column("A:A", 18)
    ws.set_column("B:B", 10)
    ws.set_column("C:C", 8)
    ws.set_column("D:G", 12)

    row = add_header(ws, workbook, "Life Expectancy and HLE Trends by Deprivation Decile",
                     "England, 2013-2015 to 2022-2024 | At birth | Male and Female")

    col_hdr = col_header_fmt(workbook)
    headers = ["Period", "IMD Decile", "Sex", "LE (years)", "HLE (years)",
               "HLE %", "Unhealthy Years"]
    for i, h in enumerate(headers):
        ws.write(row, i, h, col_hdr)
    ws.set_row(row, 22)
    row += 1

    df = le[["period", "imd_decile", "sex", "le", "hle", "hle_pct", "unhealthy_years"]].copy()
    df = df.sort_values(["sex", "period_start" if "period_start" in df.columns else "period",
                         "imd_decile"])

    num1 = data_fmt(workbook, "0.0")
    num0 = data_fmt(workbook, "0")
    text = data_fmt(workbook)
    alt = data_fmt(workbook, bg=NHS_PALE_GREY)
    alt_num = data_fmt(workbook, "0.0", bg=NHS_PALE_GREY)

    le_data = le.sort_values(["sex", "period_start", "imd_decile"])
    for i, (_, r) in enumerate(le_data.iterrows()):
        bg = NHS_PALE_GREY if i % 2 == 0 else NHS_WHITE
        f_text = data_fmt(workbook, bg=bg)
        f_num = data_fmt(workbook, "0.0", bg=bg)
        f_pct = data_fmt(workbook, "0", bg=bg)
        ws.write(row, 0, r["period"], f_text)
        ws.write(row, 1, r["imd_decile"], f_pct)
        ws.write(row, 2, r["sex"], f_text)
        ws.write(row, 3, r["le"], f_num)
        ws.write(row, 4, r["hle"], f_num)
        ws.write(row, 5, r["hle_pct"], f_pct)
        ws.write(row, 6, r["unhealthy_years"], f_num)
        row += 1

    print("  Built: Deprivation Trends sheet")


def build_la_rankings(workbook, lad):
    ws = workbook.add_worksheet("Local Authority Rankings")
    ws.set_column("A:A", 30)
    ws.set_column("B:B", 8)
    ws.set_column("C:H", 14)

    row = add_header(ws, workbook, "Local Authority Rankings by Health Outcomes and Deprivation",
                     "England | Most recent period available | Male LE at age 1-4")

    col_hdr = col_header_fmt(workbook)
    headers = ["Local Authority", "Sex", "LE Value", "IMD Avg Score",
               "IMD % Most Deprived", "Health Deprivation Score", "IMD Deprivation Decile"]
    for i, h in enumerate(headers):
        ws.write(row, i, h, col_hdr)
    ws.set_row(row, 22)
    row += 1

    df = lad.sort_values("imd_avg_score", ascending=False)
    cols = ["lad_name_le", "sex", "le_value", "imd_avg_score",
            "imd_pct_most_deprived", "health_avg_score", "imd_deprivation_decile"]
    df = df[cols].dropna(subset=["le_value"])

    for i, (_, r) in enumerate(df.iterrows()):
        bg = NHS_PALE_GREY if i % 2 == 0 else NHS_WHITE
        f_text = data_fmt(workbook, bg=bg)
        f_num = data_fmt(workbook, "0.0", bg=bg)
        f_pct = data_fmt(workbook, "0.000", bg=bg)
        ws.write(row, 0, str(r["lad_name_le"]), f_text)
        ws.write(row, 1, str(r["sex"]), f_text)
        ws.write(row, 2, r["le_value"] if pd.notna(r["le_value"]) else "", f_num)
        ws.write(row, 3, r["imd_avg_score"] if pd.notna(r["imd_avg_score"]) else "", f_num)
        ws.write(row, 4, r["imd_pct_most_deprived"] if pd.notna(r["imd_pct_most_deprived"]) else "", f_pct)
        ws.write(row, 5, r["health_avg_score"] if pd.notna(r["health_avg_score"]) else "", f_num)
        ws.write(row, 6, str(r["imd_deprivation_decile"]) if pd.notna(r["imd_deprivation_decile"]) else "", f_text)
        row += 1

    # Conditional formatting on IMD score column (col C, index 3)
    max_imd = float(df["imd_avg_score"].max())
    ws.conditional_format(5, 3, 5 + len(df), 3, {
        "type": "2_color_scale",
        "min_color": "#C6EFCE",
        "max_color": "#FF9999",
        "min_value": 0,
        "max_value": max_imd,
    })
    print("  Built: Local Authority Rankings sheet")


def build_data_sheet(workbook, le, lad, imd):
    for sheet_name, df, cols in [
        ("Data - HLE by Deprivation", le,
         ["period", "imd_decile", "sex", "le", "hle", "hle_pct", "unhealthy_years", "deprivation_label"]),
        ("Data - LA Deprivation", lad[lad["sex"].isin(["Male", "Female"])],
         ["lad_name_le", "sex", "le_value", "imd_avg_score", "imd_pct_most_deprived",
          "health_avg_score", "imd_deprivation_decile"]),
    ]:
        ws = workbook.add_worksheet(sheet_name[:31])
        row = add_header(ws, workbook, sheet_name, "Source: ONS Healthy Life Expectancy / IMD25")
        col_hdr = col_header_fmt(workbook)
        subset = df[cols].copy()
        for i, c in enumerate(subset.columns):
            ws.write(row, i, c, col_hdr)
            ws.set_column(i, i, max(len(c) + 2, 14))
        row += 1
        for _, r in subset.iterrows():
            for j, val in enumerate(r):
                ws.write(row, j, val if pd.notna(val) else "")
            row += 1
    print("  Built: Data sheets")


def run():
    le, lad, imd = load_data()
    workbook = xlsxwriter.Workbook(OUTPUT)
    workbook.set_properties({"title": "NHS Health Inequalities Analysis"})

    print("Building Excel workbook...")
    build_summary(workbook, le)
    build_deprivation_trends(workbook, le)
    build_la_rankings(workbook, lad)
    build_data_sheet(workbook, le, lad, imd)

    workbook.close()
    print(f"\nSaved: {OUTPUT}")


if __name__ == "__main__":
    run()
