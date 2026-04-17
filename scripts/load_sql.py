import pandas as pd
import pyodbc
import os

SERVER = os.environ.get("SQL_SERVER", r"DESKTOP-4BP374J\SQLEXPRESS")
DATABASE = "NHS_Health_Inequalities"
PROCESSED = "data/processed"


def get_connection(database=None):
    db_part = f";DATABASE={database}" if database else ""
    conn_str = f"DRIVER={{SQL Server}};SERVER={SERVER};Trusted_Connection=yes{db_part}"
    return pyodbc.connect(conn_str, autocommit=True)


def create_database():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = '{DATABASE}')
        CREATE DATABASE [{DATABASE}]
    """)
    conn.close()
    print(f"  Database '{DATABASE}' ready.")


CREATE_TABLES = """
IF OBJECT_ID('dbo.le_hle_by_deprivation', 'U') IS NULL
CREATE TABLE dbo.le_hle_by_deprivation (
    period              NVARCHAR(20),
    period_start        INT,
    period_end          INT,
    imd_decile          INT,
    sex                 NVARCHAR(10),
    sex_code            INT,
    age_group           NVARCHAR(10),
    age_code            INT,
    le                  FLOAT,
    le_lci              FLOAT,
    le_uci              FLOAT,
    hle                 FLOAT,
    hle_lci             FLOAT,
    hle_uci             FLOAT,
    hle_pct             FLOAT,
    unhealthy_years     FLOAT,
    deprivation_label   NVARCHAR(20)
);

IF OBJECT_ID('dbo.imd25_lad_summaries', 'U') IS NULL
CREATE TABLE dbo.imd25_lad_summaries (
    lad_code                    NVARCHAR(10),
    lad_name                    NVARCHAR(100),
    imd_avg_rank                FLOAT,
    imd_avg_score               FLOAT,
    imd_pct_most_deprived       FLOAT,
    imd_extent                  FLOAT,
    health_avg_rank             FLOAT,
    health_avg_score            FLOAT,
    health_pct_most_deprived    FLOAT
);

IF OBJECT_ID('dbo.le_by_local_authority', 'U') IS NULL
CREATE TABLE dbo.le_by_local_authority (
    le_value    FLOAT,
    le_lci      FLOAT,
    le_uci      FLOAT,
    period      NVARCHAR(20),
    lad_code    NVARCHAR(10),
    lad_name    NVARCHAR(100),
    sex         NVARCHAR(10),
    age_group   NVARCHAR(10)
);

IF OBJECT_ID('dbo.la_deprivation_merged', 'U') IS NULL
CREATE TABLE dbo.la_deprivation_merged (
    le_value                    FLOAT,
    le_lci                      FLOAT,
    le_uci                      FLOAT,
    period                      NVARCHAR(20),
    lad_code                    NVARCHAR(10),
    lad_name_le                 NVARCHAR(100),
    sex                         NVARCHAR(10),
    age_group                   NVARCHAR(10),
    lad_name_imd                NVARCHAR(100),
    imd_avg_rank                FLOAT,
    imd_avg_score               FLOAT,
    imd_pct_most_deprived       FLOAT,
    imd_extent                  FLOAT,
    health_avg_rank             FLOAT,
    health_avg_score            FLOAT,
    health_pct_most_deprived    FLOAT,
    imd_deprivation_decile      NVARCHAR(5)
);
"""


def bulk_insert(cursor, table, df):
    df = df.where(pd.notnull(df), None)
    cols = ", ".join(df.columns)
    placeholders = ", ".join(["?" for _ in df.columns])
    sql = f"INSERT INTO dbo.{table} ({cols}) VALUES ({placeholders})"
    cursor.executemany(sql, df.values.tolist())


def run():
    print("Creating database...")
    create_database()

    conn = get_connection(DATABASE)
    cursor = conn.cursor()

    print("Creating tables...")
    for stmt in CREATE_TABLES.split(";"):
        stmt = stmt.strip()
        if stmt:
            cursor.execute(stmt)
    conn.commit()

    print("Loading data...")
    tables = {
        "le_hle_by_deprivation": pd.read_csv(f"{PROCESSED}/le_hle_by_deprivation.csv"),
        "imd25_lad_summaries": pd.read_csv(f"{PROCESSED}/imd25_lad_summaries.csv"),
        "le_by_local_authority": pd.read_csv(f"{PROCESSED}/le_by_local_authority.csv"),
        "la_deprivation_merged": pd.read_csv(f"{PROCESSED}/la_deprivation_merged.csv"),
    }

    for table, df in tables.items():
        cursor.execute(f"DELETE FROM dbo.{table}")
        if table == "la_deprivation_merged":
            df.columns = [
                "le_value", "le_lci", "le_uci", "period", "lad_code",
                "lad_name_le", "sex", "age_group", "lad_name_imd",
                "imd_avg_rank", "imd_avg_score", "imd_pct_most_deprived",
                "imd_extent", "health_avg_rank", "health_avg_score",
                "health_pct_most_deprived", "imd_deprivation_decile"
            ]
        bulk_insert(cursor, table, df)
        conn.commit()
        print(f"  Loaded {table}: {len(df):,} rows")

    conn.close()
    print("\nSQL load complete.")


if __name__ == "__main__":
    run()
