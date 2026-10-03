# CONTEXT.md — handoff for anyone (or any AI) working with this dataset

> **Keep this file current.** Update it whenever a table, column, model, or the way
> data is accessed changes. Last updated: 2026-10-02 (iteration 1).

## What this is

A lakehouse built on **synthetic data for "Meridian Cloud,"** a fictional hyperscaler.
Two orgs are modeled and tied together:

- **Infrastructure supply chain** — buys components (CPUs, GPUs, memory, SSDs, NICs,
  switches, PSUs, chassis, racks, cooling) from suppliers, stages them in regional
  integration hubs, builds server racks, deploys them to cloud regions.
- **Infrastructure finance** — capitalizes racks, depreciates them, accrues data-center
  opex, pays supplier invoices, tracks everything against a budget in a general ledger.

Numbers tie out: PO receipts post to inventory and AP; rack installs post to fixed assets
and start straight-line depreciation; actual unit cost vs. standard cost posts to PPV.

- 24 months of data: **2024-10 through 2026-09**
- Seeded (`numpy` seed 42): `python generate_data.py` reproduces it byte-for-byte
- Scale: 20.7k racks / $21.6B capex, 5.1k PO lines, 430k GL lines
- Currency is USD everywhere. Dates are plain dates (no timezones).

### Baked-in stories (useful for exercises)

| Story | Where to see it |
|---|---|
| GPU vendor (**Vertex Accelerators**) runs ~52% OTIF because of allocation cuts | `fct_supplier_otif`, `purchase_orders` |
| **Meridian Flash Partners** and **Shenzhen Optics** are chronically late | `fct_supplier_otif` |
| GPU/HBM prices climb over the period; DRAM falls then recovers → big PPV | `fct_purchase_price_variance` |
| GPU racks depreciate over 48 months, everything else 72 | `rack_deployments.useful_life_months` |
| Depreciation and power were under-budgeted (~6%), the rest slightly over | `fct_budget_vs_actual` (accounts 5100, 5200) |
| 22TB HDDs sit in inventory >180 days → excess & obsolete risk | `fct_inventory_days_of_supply.is_eo_risk` |
| Tokyo (apj-2) launched 2025-04 and is served from the Singapore hub | `regions`, `rack_deployments.hub_id` |
| ~8% of supplier invoices are never paid (disputes) | `supplier_invoices.paid_date is null`, `fct_ap_aging` |

---

## How to access the data from Python (VS Code)

`from lab import rows` works **from any folder and with either Python on this machine**
(the lab's `.venv` and the main Python 3.12 install): the lab folder is registered on
both import paths via a `data-lake-lab.pth` file in each `site-packages`, and `lab.py`
locates `.env` and the data relative to itself. No `cd` needed.

Practice scripts live in `C:\Users\micha\data-lake-lab\tutorials\` and run with the ▶
button in VS Code. **`tutorials/` is gitignored** — anything in it stays local and never
reaches GitHub, so it's a safe dumping ground for scratch work.

```python
from lab import rows, sql, snowflake_sql

suppliers = rows("suppliers")                      # any BRONZE table -> list of dicts
scorecard = rows("fct_supplier_otif")              # any GOLD table  -> list of dicts (read from the R2 bucket)
small     = rows("gl_journal", limit=1000)         # cap big tables

late = sql("""                                     # any DuckDB SQL over bronze + gold tables
    select supplier_name, round(avg(otif_pct), 1) as otif_pct
    from fct_supplier_otif group by 1 order by 2
""")

aging = snowflake_sql("select * from LAKE.DEV_GOLD.FCT_AP_AGING")   # same on Snowflake
```

Every call returns **`[{"column": value, ...}, ...]`** — a list of dicts, one per row.
Column names are lowercase from `rows()`/`sql()`, **UPPERCASE from `snowflake_sql()`**.
Dates come back as `datetime.date`, booleans as `bool`, money as `float`.

To see a table's shape: `print(rows("fct_supplier_otif")[0])`.

Requirements: `.env` must be present (R2 keys; Snowflake key path), and `data/bronze/`
must exist (`python generate_data.py` if not). Internet is needed for gold tables and
Snowflake; bronze tables are local Parquet.

---

## Schema

Three layers. Bronze = raw source extracts. Silver = cleaned/joined (dbt staging).
Gold = business-ready facts (dbt marts). Keys: `*_id` and `*_code` columns join by name.

### Entity relationships

```
regions ──< hubs                     (hub serves a region; Tokyo apj-2 uses HUB-SIN)
regions ──< rack_deployments >── server_skus ──< bom >── components >── suppliers
hubs    ──< rack_deployments
hubs    ──< purchase_orders  >── components, suppliers
hubs    ──< inventory_snapshots >── components
regions ──< capacity_forecast  (by sku_family, not sku)
suppliers ──< supplier_invoices  (invoice.po_number -> purchase_orders.po_number)
cost_centers ──< gl_journal >── gl_accounts
cost_centers ──< budget     >── gl_accounts
regions ──< cost_centers   (DC Ops cost centers; others are 'global')
```

### Bronze tables (`data/bronze/<table>/*.parquet`, `s3://datalake/bronze/<table>/`, Snowflake `LAKE.BRONZE.<TABLE>`)

**regions** (6) — cloud regions
| column | type | meaning |
|---|---|---|
| region_code | str | `pnw-1`, `sea-2`, `ctx-1`, `eur-1`, `apj-1`, `apj-2` |
| region_name | str | e.g. "Pacific Northwest" |
| country | str | ISO-ish: US, IE, SG, JP |
| launched_date | str (YYYY-MM-DD) | no data before this date for the region |

**hubs** (5) — regional integration hubs where racks are built
| hub_id | str | `HUB-PDX`, `HUB-IAD`, `HUB-DFW`, `HUB-DUB`, `HUB-SIN` |
| hub_name | str | |
| region_code | str | → regions |

**suppliers** (14)
| supplier_id | str | `SUP-001` … `SUP-014` |
| supplier_name | str | |
| country | str | TW, US, KR, JP, SG, CN, DE, MX, PL |
| category | str | ODM, Silicon, Memory, Storage, Network, Power, Mechanical, Thermal |
| payment_terms_days | int | 30 / 45 / 60 |
| strategic_flag | bool | strategic suppliers ship in-full more reliably |

**components** (22) — purchasable parts
| component_id | str | `CMP-CPU-01`, `CMP-GPU-02`, `CMP-MEM-03`, … |
| component_name | str | e.g. "Vertex V300 Accelerator" |
| category | str | CPU, GPU, Memory, Storage, Network, Power, Mechanical, Thermal |
| supplier_id | str | → suppliers (single-sourced) |
| standard_cost_usd | float | the cost finance plans at; PPV is measured against it |

**server_skus** (5)
| sku_id | str | `SKU-GC-2U`, `SKU-HM-2U`, `SKU-GPU-4U`, `SKU-GPU-4U-V3`, `SKU-ST-4U` |
| sku_name | str | |
| sku_family | str | General Compute, High-Memory, GPU Accelerated, Storage Dense |
| units_per_rack | int | servers per rack (20 / 20 / 8 / 8 / 10) |

**bom** (40) — bill of materials per **server unit** (multiply by units_per_rack for a rack)
| sku_id | str | → server_skus |
| component_id | str | → components |
| qty_per_unit | int | |

Per-rack infrastructure not in `bom` (same for every rack): 1 rack frame, 2 ToR switches,
2 PDUs, 64 optics; GPU racks add 1 liquid-cooling CDU. `rack_deployments.capex_usd`
already includes it.

**purchase_orders** (5,131) — one row per PO **line**
| po_line_id | str | unique, `POL-0000001` |
| po_number | str | PO header; ~2 lines per PO; joins to supplier_invoices |
| supplier_id, component_id, hub_id | str | → |
| order_date | date | |
| promised_date | date | supplier's commit |
| received_date | date | null when `status = 'Open'` |
| qty_ordered | int | |
| qty_received | int | < qty_ordered = short shipment; 0 when Open |
| unit_cost_usd | float | actual price paid (moves with market) |
| status | str | `Closed` / `Open` |

OTIF definition used in gold: on time = `received_date <= promised_date`; in full =
`qty_received >= qty_ordered`.

**inventory_snapshots** (2,640) — month-end, per hub × component
| snapshot_date | date | last day of month |
| hub_id, component_id | str | → |
| on_hand_qty | int | |
| on_order_qty | int | ordered, not yet received |
| avg_age_days | int | HDDs skew old |

**capacity_forecast** (1,104) — demand plan in racks
| forecast_month | str (YYYY-MM-01) | |
| region_code | str | → |
| sku_family | str | |
| forecast_version | str | `P6M` (6-month-out plan) or `P1M` (1-month-out commit) |
| forecast_racks | int | |

**rack_deployments** (20,666) — one row per rack, request → live
| rack_id | str | unique, `RCK-000001` |
| region_code, hub_id, sku_id | str | → |
| sku_family | str | denormalized |
| requested_date | date | demand signal; also the month the components were consumed |
| shipped_date, installed_date, live_date | date | null if still in flight past 2026-09-30 |
| capex_usd | float | full rack cost at that month's component prices (GPU racks ≈ $2.4M) |
| useful_life_months | int | 48 (GPU) or 72 |

**supplier_invoices** (2,566) — AP
| invoice_id | str | |
| supplier_id | str | → |
| po_number | str | → purchase_orders (closed POs only) |
| invoice_date, due_date | date | due = invoice + payment_terms_days |
| paid_date | date | null = unpaid (late, disputed, or not yet due) |
| amount_usd | float | sum of received qty × unit cost on the PO |
| currency | str | always USD |

**cost_centers** (11)
| cost_center_id | str | `CC-1100` … `CC-3200` |
| cost_center_name | str | |
| org | str | Supply Chain, Data Center Ops, Finance, Engineering |
| region_code | str | → regions for DC Ops; `global` otherwise |

**gl_accounts** (14)
| account_id | str | 1200 AR, 1400 Inventory, 1500 Fixed Assets, 1590 Accum. Depreciation, 2100 AP, 4100 Revenue, 5100 Depreciation, 5200 Power & Cooling, 5300 Facilities Lease, 5400 Salaries, 5500 Freight, 5600 PPV, 5700 E&O Write-down, 5800 Professional Services |
| account_name | str | |
| account_type | str | Asset, Contra-Asset, Liability, Revenue, Opex |

**gl_journal** (429,993) — posted journal lines
| journal_id | str | unique |
| posting_date | date | |
| account_id, cost_center_id | str | → |
| amount_usd | float | **positive = debit, negative = credit** |
| source | str | PO Receipt, Capitalization, Depreciation, Accrual, Payroll, Adjustment |
| reference | str | po_line_id / rack_id / `CC-xxxx-YYYY-MM` |
| memo | str | |

**budget** (1,095) — opex budget (accounts 5xxx only)
| fiscal_month | str (YYYY-MM-01) | |
| cost_center_id, account_id | str | → |
| budget_usd | float | |

### Silver (dbt staging; DuckDB `main_silver.*`, Snowflake `LAKE.DEV_SILVER.*`)

- **stg_purchase_orders** — PO lines + supplier/component attributes + `is_on_time`, `is_in_full`, `is_otif`, `days_late`, `received_value_usd`, `ppv_usd`, `promised_month`
- **stg_gl_journal** — journal lines + account/cost-center attributes + `fiscal_month`
- **stg_rack_deployments** — racks + region name + `request_to_live_days`, `ship_to_install_days`, `monthly_depreciation_usd`, `requested_month`, `live_month`

### Gold (dbt marts; Parquet at `s3://datalake/gold/<name>.parquet`, Snowflake `LAKE.DEV_GOLD.<NAME>`)

**fct_supplier_otif** (346) — grain: supplier × promised_month
`promised_month, supplier_id, supplier_name, supplier_category, strategic_flag, po_lines, qty_ordered, qty_received, on_time_pct, in_full_pct, otif_pct, avg_days_late_when_late, received_value_usd`

**fct_purchase_price_variance** (532) — grain: component × received_month
`received_month, component_category, component_id, component_name, qty_received, standard_value_usd, actual_value_usd, ppv_usd, ppv_pct` — positive ppv = paid over standard

**fct_capacity_plan_vs_actual** (552) — grain: region × sku_family × month
`forecast_month, region_code, sku_family, plan_6m_racks, commit_1m_racks, actual_racks, variance_vs_plan, variance_vs_commit, plan_abs_pct_error, commit_abs_pct_error`

**fct_inventory_days_of_supply** (2,640) — grain: hub × component × month-end
`snapshot_date, hub_id, component_id, component_name, component_category, on_hand_qty, on_order_qty, qty_consumed, avg_monthly_consumption_3m, days_of_supply, avg_age_days, on_hand_value_usd, is_eo_risk` — days_of_supply is null when nothing was consumed in the trailing 3 months

**fct_capex_by_region** (547) — grain: region × sku_family × in_service_month
`in_service_month, region_code, region_name, sku_family, racks_in_service, capex_usd, added_monthly_depreciation_usd, avg_request_to_live_days`

**fct_budget_vs_actual** (1,095) — grain: cost_center × account × fiscal_month (opex only)
`fiscal_month, cost_center_id, cost_center_name, org, region_code, account_id, account_name, actual_usd, budget_usd, variance_usd, variance_pct` — positive variance = over budget

**fct_ap_aging** (14) — grain: supplier, as of the latest invoice date
`as_of_date, supplier_id, supplier_name, payment_terms_days, open_invoices, open_usd, current_usd, past_due_1_30_usd, past_due_31_60_usd, past_due_61_90_usd, past_due_over_90_usd`

---

## Where things live

| Thing | Location |
|---|---|
| Source generator | `generate_data.py` (edit constants at the top to change scale/behaviour) |
| Raw extracts | `data/bronze/<table>/<table>.parquet`, also `data/csv/<table>.csv` (gitignored; regenerate) |
| Lake (bronze + gold) | Cloudflare R2 bucket `datalake`; creds in `.env` |
| Loader | `ingest.py` |
| dbt project | `lakehouse/` — `dbt build` (DuckDB) or `dbt build --target snowflake` |
| Snowflake | account `WDZFJTQ-OWB53326`, db `LAKE`, warehouse `LAKE_WH`, user `LAKE_SVC` (key-pair), role `LAKE_DEV` |
| Orchestration | `pipeline/definitions.py` — `run-dagster.cmd` → http://localhost:3000 |
| Python helper | `lab.py` — `rows()`, `sql()`, `snowflake_sql()` |
| Practice scripts | `tutorials/` — **gitignored**, local only |
| Repo | https://github.com/michaelvhaug1/data-lake-lab |

## Change log

- **2026-10-02 — iteration 1.** Initial dataset (15 bronze tables), 3 silver + 7 gold
  models with 20 tests, verified on DuckDB-over-R2 and Snowflake. `lab.py` helper added.
  `tutorials/` folder created for practice scripts and gitignored.
