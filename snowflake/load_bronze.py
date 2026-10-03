r"""Load every bronze Parquet file into LAKE.BRONZE on Snowflake.

    python snowflake\load_bronze.py                 # all tables under data/bronze/
    python snowflake\load_bronze.py gl_journal      # one table

For each table: PUT the file to an internal stage, create the table from the file's
schema (INFER_SCHEMA + USING TEMPLATE), then COPY INTO with MATCH_BY_COLUMN_NAME.
That is the standard Snowflake bulk-load pattern; an external stage on your R2/S3
bucket is the same COPY with a STORAGE INTEGRATION instead of PUT.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sf import connect  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BRONZE = ROOT / "data" / "bronze"

names = sys.argv[1:]
dirs = [BRONZE / n for n in names] if names else sorted(p for p in BRONZE.iterdir() if p.is_dir())
if not dirs or not BRONZE.exists():
    raise SystemExit("Nothing to load. Run generate_data.py first.")

conn = connect(schema="BRONZE")
cur = conn.cursor()
for d in dirs:
    table = d.name.upper()
    for f in sorted(d.glob("*.parquet")):
        cur.execute(f"PUT 'file://{f.as_posix()}' @BRONZE_STAGE/{d.name}/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE")
    # IGNORE_CASE => plain uppercase column names, so unquoted SQL (and dbt) can reference them.
    cur.execute(f"""
        CREATE OR REPLACE TABLE {table}
        USING TEMPLATE (
            SELECT ARRAY_AGG(OBJECT_CONSTRUCT(*))
            FROM TABLE(INFER_SCHEMA(LOCATION => '@BRONZE_STAGE/{d.name}/', FILE_FORMAT => 'PARQUET_FMT', IGNORE_CASE => TRUE))
        )
    """)
    cur.execute(f"""
        COPY INTO {table}
        FROM @BRONZE_STAGE/{d.name}/
        FILE_FORMAT = (FORMAT_NAME = 'PARQUET_FMT')
        MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
        FORCE = TRUE
    """)
    rows = sum(r[3] for r in cur.fetchall() if isinstance(r[3], int))
    print(f"{table:22s} {rows:>9,} rows")
conn.close()
