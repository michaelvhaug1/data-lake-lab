"""Smoke test: can we reach Snowflake with the key + values in .env?

    python snowflake\check_connection.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sf import connect  # noqa: E402

conn = connect()
cur = conn.cursor()
cur.execute("select current_account(), current_user(), current_role(), current_warehouse(), current_version()")
print(dict(zip(["account", "user", "role", "warehouse", "version"], cur.fetchone())))
cur.execute("show tables in schema LAKE.BRONZE")
tables = [r[1] for r in cur.fetchall()]
print("bronze tables:", tables or "none yet (run snowflake\\load_bronze.py)")
conn.close()
