# Snowflake track

Same dbt models as the DuckDB lake, run on Snowflake. Everything below the first step
is already written; the trial signup is the only part that needs you.

## 1. Create the trial  (you)

https://signup.snowflake.com — pick **Enterprise** edition, **AWS**, **US West (Oregon)**
(closest region; cloud/region can't be changed later). 30 days / $400 credits.
Personal email is fine.

After the activation email, in Snowsight:
- bottom-left account menu → **Account** → copy the **account identifier** (`ORGNAME-ACCOUNTNAME`)
- note the username you chose

Put `SNOWFLAKE_ACCOUNT` and `SNOWFLAKE_USER` in `.env`. No password: the lab uses
**key-pair auth** (`snowflake/rsa_key.p8`, gitignored), which is how service connections
are done in practice and sidesteps Snowflake's MFA requirement on password logins.

## 2. Set up the account  (DONE Oct 2 2026 — kept for rebuilding from scratch)

The Snowflake web UI runs one statement at a time unless you select everything, so the
setup is driven from the laptop instead:

1. In the web UI, run `02_service_user.sql` → creates `LAKE_SVC` (TYPE=SERVICE) with
   the laptop's public key. Then `GRANT ROLE ACCOUNTADMIN TO USER LAKE_SVC;` temporarily.
2. `python snowflake\setup_from_laptop.py` → runs every statement in `00_setup.sql`:
   credit-capped resource monitor, X-Small warehouse with 60 s auto-suspend, `LAKE`
   database, `LAKE_DEV` role + grants, Parquet file format, internal stage.
3. `REVOKE ROLE ACCOUNTADMIN FROM USER LAKE_SVC;` → the pipeline user keeps only `LAKE_DEV`.

Gotcha that cost an hour: Google sign-in created the personal user with a **lowercase**
name, and Snowflake's key-pair auth uppercases the username in the token, so the key
never matched ("JWT token is invalid"). A service user with a normal uppercase name is
the fix, and the right design anyway.

## 3. From the lab shell  (verified: 30/30 on both engines)

```
python snowflake\check_connection.py     # proves key-pair auth + role + warehouse
python generate_data.py                  # if data\bronze is empty
python snowflake\load_bronze.py          # PUT + INFER_SCHEMA(IGNORE_CASE) + COPY INTO, all 15 LAKE.BRONZE tables
cd lakehouse
dbt build --target snowflake             # same silver + gold + tests -> LAKE.DEV_SILVER / LAKE.DEV_GOLD
```

Portability notes from the first Snowflake run: `date_diff` → `datediff` (both engines
accept the latter); the `external` materialization is DuckDB-only, so `dbt_project.yml`
switches marts to `table` on Snowflake; INFER_SCHEMA needs `IGNORE_CASE => TRUE` or
you get case-sensitive lowercase column names that unquoted SQL can't see.

## What to learn here that DuckDB can't teach

These are the things interviewers actually ask about Snowflake:

- **Warehouses & credits** — resize `LAKE_WH` to SMALL, rerun `dbt build`, compare
  `QUERY_HISTORY` timings and credits. Understand why auto-suspend matters.
- **Stages, `COPY INTO`, `INFER_SCHEMA`, Snowpipe** — `load_bronze.py` uses an internal
  stage and schema inference; the next step is an **external stage** on your R2 bucket
  with a `STORAGE INTEGRATION`, then a Snowpipe that auto-ingests new files.
- **Time Travel & zero-copy clone** — `CREATE TABLE x CLONE y`, `SELECT ... AT(OFFSET => -600)`.
- **Streams & Tasks** — Snowflake-native CDC + scheduling; compare with Dagster.
- **Iceberg tables** — point Snowflake at Parquet in your own bucket; this is where the
  industry is heading and it ties the two halves of this lab together.
- **dbt on Snowflake** — incremental models with `merge`, `+transient`, query tags,
  `snapshots/` for SCD type 2.

## Cost reality

X-Small ≈ 1 credit/hour **only while running**. An hour of `dbt build` iterations on this
dataset (430k GL lines is the big table) costs well under $1. The monitor suspends the account at 300 credits;
you will not get near it unless a warehouse is left running on a loop.
