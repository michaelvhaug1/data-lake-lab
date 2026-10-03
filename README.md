# data-lake-lab — Meridian Cloud infrastructure supply chain & finance

A lakehouse built on synthetic data for a fictional hyperscaler: the org that buys
servers, GPUs, memory and network gear, builds racks in regional hubs, deploys them to
data centers, and the finance org that capitalizes, depreciates and budgets all of it.

```
generate_data.py ──▶ data/bronze/*.parquet ──ingest.py──▶ object store   bronze/   15 raw tables
                                                              │
                                              dbt-duckdb (DuckDB engine)   silver/   stg_purchase_orders, stg_gl_journal, stg_rack_deployments
                                                              │
                                                              └──▶ back to the lake  gold/   7 fact tables (Parquet)
Dagster orchestrates all of it: source_files ─▶ bronze/* ─▶ silver/* ─▶ gold/*
```

## The data  (24 months, Oct 2024 – Sep 2026, seeded so it regenerates identically)

| Table | Rows | What it is |
|---|---|---|
| `regions`, `hubs` | 6, 5 | Cloud regions and the integration hubs that serve them |
| `suppliers` | 14 | ODMs, silicon, memory, storage, network, power, mechanical, thermal; payment terms, strategic flag |
| `components`, `bom`, `server_skus` | 22, 40, 5 | Parts with standard cost; bill of materials per SKU (general compute, high-memory, GPU, storage) |
| `purchase_orders` | 5.1k lines | Promised vs received date/qty → OTIF; actual unit cost vs standard → PPV |
| `inventory_snapshots` | 2.6k | Month-end on-hand / on-order / age per hub and component |
| `capacity_forecast` | 1.1k | Rack demand by region & family; P6M plan and P1M commit versions |
| `rack_deployments` | 20.7k racks | Request → ship → install → live; capex and useful life ($21.6B total) |
| `supplier_invoices` | 2.6k | AP invoices tied to POs, with payment behaviour |
| `cost_centers`, `gl_accounts` | 11, 14 | Supply chain / DC ops / finance / engineering orgs; asset, liability, opex accounts |
| `gl_journal` | 430k lines | Receipts → inventory & AP, PPV, capitalization, straight-line depreciation, opex accruals, E&O |
| `budget` | 1.1k | Monthly opex budget by cost center and account |

Built-in stories: the GPU vendor runs ~53% OTIF because of allocation cuts; one flash
supplier is chronically late; GPU/HBM prices climb while DRAM cycles down (PPV); GPU
racks depreciate over 4 years vs 6; power and depreciation were under-budgeted.

## Gold tables

| Model | Question it answers |
|---|---|
| `fct_supplier_otif` | Supplier scorecard: on-time %, in-full %, OTIF %, days late, by month |
| `fct_purchase_price_variance` | Where are we paying over standard, by component/month |
| `fct_capacity_plan_vs_actual` | Forecast accuracy: 6-month plan vs 1-month commit vs actual racks |
| `fct_inventory_days_of_supply` | Days of supply and E&O risk per hub/component |
| `fct_capex_by_region` | Racks in service, capex, added depreciation, request-to-live cycle time |
| `fct_budget_vs_actual` | Monthly close variance by cost center and account |
| `fct_ap_aging` | Open payables by aging bucket per supplier |

## Targets

The object store is whatever `.env` points at. Verified against both:

| Target | `.env` | Notes |
|---|---|---|
| **Cloudflare R2** (current) | bucket `datalake` | free tier, zero egress; token is scoped to the one bucket so `ListBuckets` is denied by design |
| **Local MinIO** | copy `.env.local-minio` over the AWS_*/S3_*/LAKE_BUCKET lines | offline; run `start-minio.cmd` first |

Snowflake is a second **engine** (same models): see `snowflake/README.md`.

## Daily use

| Step | Command |
|---|---|
| Open a lab shell | double-click `shell.cmd` (venv + tools + env vars on PATH) |
| Regenerate source data | `python generate_data.py` |
| Land it in the lake | `python ingest.py` |
| Build silver + gold + tests | `cd lakehouse && dbt build` |
| Browse the bucket | `aws s3 ls s3://datalake --recursive` |
| Query the warehouse | `duckdb warehouse.duckdb` → `select * from main_gold.fct_supplier_otif limit 5;` |
| Orchestrate with a UI | `run-dagster.cmd` → http://localhost:3000 → Materialize all |
| (MinIO only) object store | `start-minio.cmd`; console http://localhost:9001, `lakeadmin` / `lakeadmin123` |

## Layout

```
.env                     creds/endpoint (gitignored)      .env.local-minio  offline settings
generate_data.py         synthetic Meridian Cloud data -> data/bronze/<table>/*.parquet + data/csv/
ingest.py                bronze loader (boto3)
lakehouse/               dbt project (profiles.yml has duckdb + snowflake targets)
  models/sources.yml     15 bronze sources, read in place from S3 via external_location
  models/staging/        silver        models/marts/  gold (materialized='external' -> Parquet in the lake)
  tests/generic/         range + unique-combination tests (no package dependency)
pipeline/definitions.py  Dagster: source_files -> bronze/* -> dbt assets
snowflake/               setup SQL, key-pair auth, loader, README
tools/minio/             minio.exe, mc.exe
```

## Things worth doing next

- Incremental `gl_journal` staging (`materialized='incremental'` on `posting_date`) — the table is the only one big enough to matter, which is exactly how it goes at work.
- A `dim_date` and a `snapshots/` SCD2 on `suppliers` (payment terms change).
- Partition gold by month and backfill with Dagster partitions.
- Snowflake external stage reading this R2 bucket directly (storage integration), then Snowpipe.
- Put a BI tool on gold (Evidence, Metabase, or Power BI over the Parquet) and build the supplier scorecard and monthly close pages.
