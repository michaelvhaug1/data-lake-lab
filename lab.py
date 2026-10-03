"""Tutorial helper: get real Meridian Cloud data as plain Python lists of dicts.

    from lab import rows, sql, snowflake_sql

    suppliers = rows("suppliers")                       # bronze table -> list of dicts
    otif      = rows("fct_supplier_otif")               # gold table (from the R2 bucket) -> list of dicts
    late      = sql("select * from fct_supplier_otif where otif_pct < 70")   # any DuckDB SQL
    sf        = snowflake_sql("select * from LAKE.DEV_GOLD.FCT_AP_AGING")     # same, but Snowflake

Everything comes back as [{"col": value, ...}, ...], same shape as the tutorial dicts.
"""
import os
from pathlib import Path

import duckdb
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

BRONZE = ROOT / "data" / "bronze"
BUCKET = os.getenv("LAKE_BUCKET", "lake")


def _con():
    con = duckdb.connect()
    con.execute("install httpfs; load httpfs;")
    con.execute(f"set s3_endpoint='{os.getenv('S3_ENDPOINT', 'localhost:9000')}'")
    con.execute(f"set s3_access_key_id='{os.getenv('AWS_ACCESS_KEY_ID', '')}'")
    con.execute(f"set s3_secret_access_key='{os.getenv('AWS_SECRET_ACCESS_KEY', '')}'")
    con.execute(f"set s3_use_ssl={os.getenv('S3_USE_SSL', 'false')}")
    con.execute("set s3_url_style='path'")
    con.execute(f"set s3_region='{os.getenv('AWS_DEFAULT_REGION', 'us-east-1')}'")
    # Every bronze table (local Parquet) and every gold table (Parquet in the bucket) as a view.
    for d in sorted(p for p in BRONZE.iterdir() if p.is_dir()):
        con.execute(f"create view {d.name} as select * from read_parquet('{(d / '*.parquet').as_posix()}')")
    for g in ("fct_supplier_otif", "fct_purchase_price_variance", "fct_capacity_plan_vs_actual",
              "fct_inventory_days_of_supply", "fct_capex_by_region", "fct_budget_vs_actual", "fct_ap_aging"):
        con.execute(f"create view {g} as select * from read_parquet('s3://{BUCKET}/gold/{g}.parquet')")
    return con


def _dicts(cur):
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def sql(query: str) -> list[dict]:
    """Run DuckDB SQL over the bronze + gold tables; returns a list of dicts."""
    return _dicts(_con().execute(query))


def rows(table: str, limit: int | None = None) -> list[dict]:
    """A whole table (bronze or gold) as a list of dicts."""
    return sql(f"select * from {table}" + (f" limit {limit}" if limit else ""))


def snowflake_sql(query: str) -> list[dict]:
    """Run SQL on Snowflake (LAKE.BRONZE / DEV_SILVER / DEV_GOLD); returns a list of dicts."""
    import sys
    sys.path.insert(0, str(ROOT / "snowflake"))
    from sf import connect
    con = connect()
    try:
        return _dicts(con.cursor().execute(query))
    finally:
        con.close()
