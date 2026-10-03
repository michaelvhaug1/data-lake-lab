# ============================================================
# STRETCH - SAME DICT SKILLS, REAL DATA
# ============================================================
# Run with the lab venv (bottom-right of VS Code should say .venv).

from lab import rows, sql, snowflake_sql

# ------------------------------------------------------------
# The gold supplier scorecard is just a list of dicts, like `departments`.
# ------------------------------------------------------------
scorecard = rows("fct_supplier_otif")
print(len(scorecard), "rows")
print(scorecard[0])            # one dict: promised_month, supplier_name, otif_pct, ...

# ------------------------------------------------------------
# Exactly the Level 2 pattern: loop, calculate, write a field, print.
# ------------------------------------------------------------
for row in scorecard[:5]:
    if row["otif_pct"] >= 90:
        row["grade"] = "A"
    elif row["otif_pct"] >= 80:
        row["grade"] = "B"
    else:
        row["grade"] = "C"
    print(row["supplier_name"], row["otif_pct"], row["grade"])

# ------------------------------------------------------------
# Or let SQL do the heavy lifting and loop over the result.
# ------------------------------------------------------------
worst = sql("""
    select supplier_name, round(avg(otif_pct), 1) as otif_pct
    from fct_supplier_otif
    group by 1 order by 2 limit 3
""")
for row in worst:
    print(row["supplier_name"], row["otif_pct"])

# ------------------------------------------------------------
# Same thing on Snowflake (uncomment; takes ~2s to connect).
# ------------------------------------------------------------
# aging = snowflake_sql("select supplier_name, open_usd, past_due_over_90_usd from LAKE.DEV_GOLD.FCT_AP_AGING")
# for row in aging:
#     print(row["SUPPLIER_NAME"], row["OPEN_USD"])     # Snowflake upper-cases column names
