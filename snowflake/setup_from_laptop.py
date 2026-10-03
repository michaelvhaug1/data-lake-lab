r"""Run 00_setup.sql statement-by-statement from the laptop as LAKE_SVC (needs ACCOUNTADMIN temporarily).

    python snowflake\setup_from_laptop.py
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sf import connect  # noqa: E402

sql = Path(__file__).with_name("00_setup.sql").read_text()
sql = re.sub(r"--[^\n]*", "", sql)                      # strip comments first, then split
statements = [s.strip() for s in sql.split(";") if s.strip()]

conn = connect(role="ACCOUNTADMIN", warehouse=None, database=None)
cur = conn.cursor()
failed = 0
for stmt in statements:
    try:
        cur.execute(stmt)
        print(f"OK   {stmt.splitlines()[0][:80]}")
    except Exception as e:  # noqa: BLE001
        failed += 1
        print(f"FAIL {stmt.splitlines()[0][:80]}\n     {str(e).splitlines()[-1][:120]}")
conn.close()
print("done," if not failed else f"done, {failed} failed;", f"{len(statements)} statements")
