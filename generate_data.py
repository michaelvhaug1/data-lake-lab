"""Synthetic data for Meridian Cloud: a fictional hyperscaler's infrastructure
supply chain and the finance org that funds it.

    python generate_data.py            # writes data/bronze/<table>/<table>.parquet and data/csv/<table>.csv

Deterministic (seeded). ~24 months ending 2026-09. Designed so the numbers tie out:
POs -> supplier invoices -> AP + inventory; rack deployments -> capex -> depreciation;
everything rolls into the GL against a budget.
"""
from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
ROOT = Path(__file__).resolve().parent
OUT_PQ = ROOT / "data" / "bronze"
OUT_CSV = ROOT / "data" / "csv"
MONTHS = pd.period_range("2024-10", "2026-09", freq="M")
START, END = MONTHS[0].start_time, MONTHS[-1].end_time.normalize()

# ---------------------------------------------------------------- reference data
regions = pd.DataFrame([
    ("pnw-1", "Pacific Northwest", "US", "2019-03-01", 1.00),
    ("sea-2", "US East (Virginia)", "US", "2017-06-01", 1.35),
    ("ctx-1", "US Central (Texas)", "US", "2023-01-15", 0.70),
    ("eur-1", "EU West (Dublin)", "IE", "2018-09-01", 0.80),
    ("apj-1", "Asia Pacific (Singapore)", "SG", "2020-02-01", 0.55),
    ("apj-2", "Asia Pacific (Tokyo)", "JP", "2025-04-01", 0.30),
], columns=["region_code", "region_name", "country", "launched_date", "demand_weight"])

hubs = pd.DataFrame([
    ("HUB-PDX", "Portland Integration Hub", "pnw-1"),
    ("HUB-IAD", "Ashburn Integration Hub", "sea-2"),
    ("HUB-DFW", "Dallas Integration Hub", "ctx-1"),
    ("HUB-DUB", "Dublin Integration Hub", "eur-1"),
    ("HUB-SIN", "Singapore Integration Hub", "apj-1"),
], columns=["hub_id", "hub_name", "region_code"])
# Tokyo is served from Singapore until its own hub opens.
region_hub = dict(zip(hubs.region_code, hubs.hub_id)) | {"apj-2": "HUB-SIN"}

suppliers = pd.DataFrame([
    # id, name, country, category, payment terms, strategic, base on-time prob, lead time days
    ("SUP-001", "Quantum Dynamics Mfg", "TW", "ODM", 60, True, 0.92, 45),
    ("SUP-002", "Pacific Rim Systems", "TW", "ODM", 60, True, 0.88, 50),
    ("SUP-003", "Helios Semiconductor", "US", "Silicon", 45, True, 0.95, 90),
    ("SUP-004", "Vertex Accelerators", "US", "Silicon", 30, True, 0.71, 120),   # GPU vendor, allocation-constrained
    ("SUP-005", "Nordlicht Memory", "KR", "Memory", 45, True, 0.90, 60),
    ("SUP-006", "Sakura DRAM Co", "JP", "Memory", 45, False, 0.85, 65),
    ("SUP-007", "Granite Storage", "US", "Storage", 45, True, 0.93, 40),
    ("SUP-008", "Meridian Flash Partners", "SG", "Storage", 30, False, 0.78, 55),  # chronically late
    ("SUP-009", "Fiberline Networks", "US", "Network", 45, True, 0.91, 35),
    ("SUP-010", "Shenzhen Optics", "CN", "Network", 30, False, 0.80, 70),
    ("SUP-011", "Atlas Power Systems", "DE", "Power", 60, False, 0.94, 30),
    ("SUP-012", "Keystone Metalworks", "MX", "Mechanical", 60, False, 0.89, 25),
    ("SUP-013", "Baltic Rack Co", "PL", "Mechanical", 45, False, 0.86, 40),
    ("SUP-014", "Coolant Engineering", "US", "Thermal", 45, False, 0.90, 35),
], columns=["supplier_id", "supplier_name", "country", "category", "payment_terms_days",
            "strategic_flag", "_otp", "_lead"])

components = pd.DataFrame([
    ("CMP-CPU-01", "Helios H9 64-core CPU", "CPU", "SUP-003", 3200.0),
    ("CMP-CPU-02", "Helios H9 96-core CPU", "CPU", "SUP-003", 4900.0),
    ("CMP-GPU-01", "Vertex V200 Accelerator", "GPU", "SUP-004", 24000.0),
    ("CMP-GPU-02", "Vertex V300 Accelerator", "GPU", "SUP-004", 31000.0),
    ("CMP-MEM-01", "64GB DDR5 RDIMM", "Memory", "SUP-005", 210.0),
    ("CMP-MEM-02", "128GB DDR5 RDIMM", "Memory", "SUP-006", 455.0),
    ("CMP-MEM-03", "HBM3 Stack (per GPU)", "Memory", "SUP-005", 1800.0),
    ("CMP-SSD-01", "3.84TB NVMe SSD", "Storage", "SUP-007", 410.0),
    ("CMP-SSD-02", "15.36TB NVMe SSD", "Storage", "SUP-007", 1350.0),
    ("CMP-HDD-01", "22TB Nearline HDD", "Storage", "SUP-008", 330.0),
    ("CMP-NIC-01", "100GbE NIC", "Network", "SUP-009", 620.0),
    ("CMP-NIC-02", "400GbE NIC", "Network", "SUP-009", 1450.0),
    ("CMP-OPT-01", "400G Optical Transceiver", "Network", "SUP-010", 480.0),
    ("CMP-SW-01", "Top-of-Rack Switch 32x400G", "Network", "SUP-009", 18500.0),
    ("CMP-PSU-01", "3kW Titanium PSU", "Power", "SUP-011", 390.0),
    ("CMP-PDU-01", "Rack PDU 30kW", "Power", "SUP-011", 2100.0),
    ("CMP-CHS-01", "2U Compute Chassis", "Mechanical", "SUP-001", 850.0),
    ("CMP-CHS-02", "4U GPU Chassis", "Mechanical", "SUP-002", 2400.0),
    ("CMP-CHS-03", "4U Storage Chassis 36-bay", "Mechanical", "SUP-001", 1900.0),
    ("CMP-RCK-01", "48U Rack Frame", "Mechanical", "SUP-013", 1600.0),
    ("CMP-CDU-01", "Rack Liquid Cooling CDU", "Thermal", "SUP-014", 14000.0),
    ("CMP-FAN-01", "High-static Fan Module", "Thermal", "SUP-012", 45.0),
], columns=["component_id", "component_name", "category", "supplier_id", "standard_cost_usd"])

server_skus = pd.DataFrame([
    ("SKU-GC-2U", "General Compute 2U", "General Compute", 20),
    ("SKU-HM-2U", "High-Memory 2U", "High-Memory", 20),
    ("SKU-GPU-4U", "GPU Accelerated 4U (8x V200)", "GPU Accelerated", 8),
    ("SKU-GPU-4U-V3", "GPU Accelerated 4U (8x V300)", "GPU Accelerated", 8),
    ("SKU-ST-4U", "Storage Dense 4U", "Storage Dense", 10),
], columns=["sku_id", "sku_name", "sku_family", "units_per_rack"])

bom = pd.DataFrame([
    # sku, component, qty per server unit
    ("SKU-GC-2U", "CMP-CPU-01", 2), ("SKU-GC-2U", "CMP-MEM-01", 16), ("SKU-GC-2U", "CMP-SSD-01", 2),
    ("SKU-GC-2U", "CMP-NIC-01", 1), ("SKU-GC-2U", "CMP-PSU-01", 2), ("SKU-GC-2U", "CMP-CHS-01", 1), ("SKU-GC-2U", "CMP-FAN-01", 6),
    ("SKU-HM-2U", "CMP-CPU-02", 2), ("SKU-HM-2U", "CMP-MEM-02", 24), ("SKU-HM-2U", "CMP-SSD-01", 2),
    ("SKU-HM-2U", "CMP-NIC-01", 1), ("SKU-HM-2U", "CMP-PSU-01", 2), ("SKU-HM-2U", "CMP-CHS-01", 1), ("SKU-HM-2U", "CMP-FAN-01", 6),
    ("SKU-GPU-4U", "CMP-CPU-02", 2), ("SKU-GPU-4U", "CMP-GPU-01", 8), ("SKU-GPU-4U", "CMP-MEM-03", 8), ("SKU-GPU-4U", "CMP-MEM-02", 16),
    ("SKU-GPU-4U", "CMP-SSD-02", 4), ("SKU-GPU-4U", "CMP-NIC-02", 4), ("SKU-GPU-4U", "CMP-PSU-01", 4), ("SKU-GPU-4U", "CMP-CHS-02", 1), ("SKU-GPU-4U", "CMP-FAN-01", 10),
    ("SKU-GPU-4U-V3", "CMP-CPU-02", 2), ("SKU-GPU-4U-V3", "CMP-GPU-02", 8), ("SKU-GPU-4U-V3", "CMP-MEM-03", 8), ("SKU-GPU-4U-V3", "CMP-MEM-02", 16),
    ("SKU-GPU-4U-V3", "CMP-SSD-02", 4), ("SKU-GPU-4U-V3", "CMP-NIC-02", 4), ("SKU-GPU-4U-V3", "CMP-PSU-01", 4), ("SKU-GPU-4U-V3", "CMP-CHS-02", 1), ("SKU-GPU-4U-V3", "CMP-FAN-01", 10),
    ("SKU-ST-4U", "CMP-CPU-01", 1), ("SKU-ST-4U", "CMP-MEM-01", 8), ("SKU-ST-4U", "CMP-HDD-01", 36), ("SKU-ST-4U", "CMP-SSD-01", 2),
    ("SKU-ST-4U", "CMP-NIC-01", 2), ("SKU-ST-4U", "CMP-PSU-01", 2), ("SKU-ST-4U", "CMP-CHS-03", 1), ("SKU-ST-4U", "CMP-FAN-01", 8),
], columns=["sku_id", "component_id", "qty_per_unit"])
# Per-rack infrastructure, same for every rack.
RACK_INFRA = {"CMP-RCK-01": 1, "CMP-SW-01": 2, "CMP-PDU-01": 2, "CMP-OPT-01": 64}
GPU_RACK_INFRA = {"CMP-CDU-01": 1}

cost_centers = pd.DataFrame([
    ("CC-1100", "Infrastructure Supply Chain", "Supply Chain", "global"),
    ("CC-1200", "Capacity Planning", "Supply Chain", "global"),
    ("CC-1300", "Supplier Management", "Supply Chain", "global"),
    ("CC-2100", "DC Operations - PNW", "Data Center Ops", "pnw-1"),
    ("CC-2200", "DC Operations - US East", "Data Center Ops", "sea-2"),
    ("CC-2300", "DC Operations - US Central", "Data Center Ops", "ctx-1"),
    ("CC-2400", "DC Operations - EU", "Data Center Ops", "eur-1"),
    ("CC-2500", "DC Operations - APJ", "Data Center Ops", "apj-1"),
    ("CC-2600", "DC Operations - Tokyo", "Data Center Ops", "apj-2"),
    ("CC-3100", "Infrastructure Finance", "Finance", "global"),
    ("CC-3200", "Network Engineering", "Engineering", "global"),
], columns=["cost_center_id", "cost_center_name", "org", "region_code"])
region_cc = {r: c for c, r in zip(cost_centers.cost_center_id, cost_centers.region_code) if r != "global"}

gl_accounts = pd.DataFrame([
    ("1200", "Accounts Receivable", "Asset"),
    ("1400", "Inventory - Components", "Asset"),
    ("1500", "Fixed Assets - Servers & Racks", "Asset"),
    ("1590", "Accumulated Depreciation", "Contra-Asset"),
    ("2100", "Accounts Payable", "Liability"),
    ("4100", "Infrastructure Revenue (Internal Transfer)", "Revenue"),
    ("5100", "Depreciation Expense", "Opex"),
    ("5200", "DC Power & Cooling", "Opex"),
    ("5300", "DC Facilities Lease", "Opex"),
    ("5400", "Salaries & Benefits", "Opex"),
    ("5500", "Freight & Logistics", "Opex"),
    ("5600", "Purchase Price Variance", "Opex"),
    ("5700", "Inventory Write-down / E&O", "Opex"),
    ("5800", "Professional Services", "Opex"),
], columns=["account_id", "account_name", "account_type"])

# ---------------------------------------------------------------- component price index (market movement)
# Multiplier on standard cost by month. GPUs and DRAM move; everything else drifts.
price_idx = {}
for cid, cat in zip(components.component_id, components.category):
    t = np.arange(len(MONTHS))
    if cat == "GPU":
        path = 1.0 + 0.012 * t + 0.03 * np.sin(t / 3)            # allocation premium climbs
    elif cat == "Memory":
        path = 1.0 - 0.015 * t + 0.08 * np.sin(t / 4 + 1)        # DRAM cycle: falls then recovers
    else:
        path = 1.0 + rng.normal(0, 0.004, len(t)).cumsum()
    price_idx[cid] = dict(zip(MONTHS, np.clip(path, 0.6, 1.6)))

# ---------------------------------------------------------------- capacity forecast & rack deployments
fam_mix = {"General Compute": 0.42, "High-Memory": 0.12, "GPU Accelerated": 0.31, "Storage Dense": 0.15}
BASE_RACKS_PER_MONTH = 140
growth = np.linspace(1.0, 1.55, len(MONTHS))                    # demand ramps over 2 years
gpu_ramp = np.linspace(0.7, 1.6, len(MONTHS))                   # GPU share grows

fc_rows, dep_rows, rack_seq = [], [], 0
for mi, m in enumerate(MONTHS):
    for _, r in regions.iterrows():
        if pd.Timestamp(r.launched_date) > m.end_time:
            continue
        for fam, share in fam_mix.items():
            mult = gpu_ramp[mi] if fam == "GPU Accelerated" else 1.0
            expected = BASE_RACKS_PER_MONTH * r.demand_weight * share * growth[mi] * mult
            # Two forecast versions: a 6-month-out plan and a 1-month-out commit.
            fc_rows.append((m.strftime("%Y-%m-01"), r.region_code, fam, "P6M", int(round(expected * rng.normal(1.0, 0.18)))))
            fc_rows.append((m.strftime("%Y-%m-01"), r.region_code, fam, "P1M", int(round(expected * rng.normal(1.0, 0.07)))))
            actual = int(round(expected * rng.normal(0.96 if fam == "GPU Accelerated" else 1.0, 0.10)))
            for _ in range(max(actual, 0)):
                rack_seq += 1
                if fam == "GPU Accelerated":
                    sku = "SKU-GPU-4U-V3" if (mi > 12 and rng.random() < 0.6) else "SKU-GPU-4U"
                else:
                    sku = server_skus.set_index("sku_family").loc[fam, "sku_id"]
                requested = m.start_time + pd.Timedelta(days=int(rng.integers(0, 28)))
                ship_lag = int(rng.gamma(3, 6)) + (10 if fam == "GPU Accelerated" else 0)
                shipped = requested + pd.Timedelta(days=ship_lag)
                installed = shipped + pd.Timedelta(days=int(rng.gamma(2, 4)) + 3)
                live = installed + pd.Timedelta(days=int(rng.gamma(2, 3)) + 1)
                dep_rows.append((f"RCK-{rack_seq:06d}", r.region_code, region_hub[r.region_code], sku, fam,
                                 requested.date(), shipped.date(), installed.date(), live.date()))

capacity_forecast = pd.DataFrame(fc_rows, columns=["forecast_month", "region_code", "sku_family", "forecast_version", "forecast_racks"])
rack_deployments = pd.DataFrame(dep_rows, columns=["rack_id", "region_code", "hub_id", "sku_id", "sku_family",
                                                   "requested_date", "shipped_date", "installed_date", "live_date"])
# Future-dated racks past the data window stay "in flight".
for c in ("shipped_date", "installed_date", "live_date"):
    rack_deployments[c] = pd.to_datetime(rack_deployments[c])
    rack_deployments.loc[rack_deployments[c] > END, c] = pd.NaT

# Rack capex = BOM at the month's actual component prices.
units = server_skus.set_index("sku_id").units_per_rack
std_cost = components.set_index("component_id").standard_cost_usd
bom_by_sku = {s: dict(zip(g.component_id, g.qty_per_unit)) for s, g in bom.groupby("sku_id")}

def rack_cost(sku, month, fam):
    comp = {k: v * units[sku] for k, v in bom_by_sku[sku].items()} | RACK_INFRA
    if fam == "GPU Accelerated":
        comp |= GPU_RACK_INFRA
    return float(sum(std_cost[c] * price_idx[c][month] * q for c, q in comp.items()))

req_month = pd.to_datetime(rack_deployments.requested_date).dt.to_period("M")
rack_deployments["capex_usd"] = [round(rack_cost(s, m, f) * rng.normal(1.0, 0.02), 2)
                                 for s, m, f in zip(rack_deployments.sku_id, req_month, rack_deployments.sku_family)]
rack_deployments["useful_life_months"] = np.where(rack_deployments.sku_family == "GPU Accelerated", 48, 72)

# ---------------------------------------------------------------- purchase orders (component demand from racks, ordered a lead time ahead)
sup = suppliers.set_index("supplier_id")
comp_sup = components.set_index("component_id").supplier_id
demand = {}  # (month, hub, component) -> qty
for _, d in rack_deployments.iterrows():
    m = pd.Period(d.requested_date, freq="M")
    comp = {k: v * units[d.sku_id] for k, v in bom_by_sku[d.sku_id].items()} | RACK_INFRA
    if d.sku_family == "GPU Accelerated":
        comp |= GPU_RACK_INFRA
    for c, q in comp.items():
        demand[(m, d.hub_id, c)] = demand.get((m, d.hub_id, c), 0) + q

po_rows, po_seq = [], 0
for (m, hub, c), qty in sorted(demand.items()):
    s = comp_sup[c]
    lead = sup.loc[s, "_lead"]
    # Order enough for the month's demand plus safety stock, split into 1-3 PO lines.
    total = int(qty * rng.normal(1.08, 0.06))
    n_lines = int(rng.integers(1, 4))
    splits = rng.multinomial(total, np.ones(n_lines) / n_lines)
    for q in splits:
        if q <= 0:
            continue
        po_seq += 1
        need_by = m.start_time + pd.Timedelta(days=int(rng.integers(0, 20)))
        order_date = need_by - pd.Timedelta(days=int(lead * rng.normal(1.0, 0.1)))
        promised = order_date + pd.Timedelta(days=int(lead))
        on_time = rng.random() < sup.loc[s, "_otp"]
        slip = 0 if on_time else int(rng.gamma(2, 7)) + 1
        received = promised + pd.Timedelta(days=slip - int(rng.integers(0, 3)))
        in_full = rng.random() < (0.97 if sup.loc[s, "strategic_flag"] else 0.90)
        qty_recv = int(q) if in_full else int(q * rng.uniform(0.6, 0.97))
        if c.startswith("CMP-GPU") and rng.random() < 0.25:         # GPU allocation cuts
            qty_recv = int(qty_recv * rng.uniform(0.5, 0.9))
        unit_cost = round(std_cost[c] * price_idx[c][min(max(pd.Period(order_date, "M"), MONTHS[0]), MONTHS[-1])] * rng.normal(1.0, 0.015), 2)
        status = "Closed"
        if received > END:
            received, qty_recv, status = pd.NaT, 0, "Open"
        po_rows.append((f"POL-{po_seq:07d}", f"PO-{100000 + po_seq // 2}", s, c, hub, order_date.date(), promised.date(),
                        received.date() if pd.notna(received) else None, int(q), qty_recv, unit_cost, status))
purchase_orders = pd.DataFrame(po_rows, columns=["po_line_id", "po_number", "supplier_id", "component_id", "hub_id",
                                                 "order_date", "promised_date", "received_date", "qty_ordered",
                                                 "qty_received", "unit_cost_usd", "status"])

# ---------------------------------------------------------------- inventory snapshots (month-end, per hub/component)
po_m = purchase_orders.assign(recv_m=pd.to_datetime(purchase_orders.received_date).dt.to_period("M"),
                              ord_m=pd.to_datetime(purchase_orders.order_date).dt.to_period("M"))
inv_rows = []
for hub in hubs.hub_id:
    for c in components.component_id:
        on_hand = int(std_cost[c] < 1000) * int(rng.integers(50, 400)) + int(rng.integers(5, 40))
        for m in MONTHS:
            recv = po_m[(po_m.hub_id == hub) & (po_m.component_id == c) & (po_m.recv_m == m)].qty_received.sum()
            used = demand.get((m, hub, c), 0)
            on_hand = max(on_hand + int(recv) - int(used), 0)
            on_order = po_m[(po_m.hub_id == hub) & (po_m.component_id == c) & (po_m.ord_m <= m) & ((po_m.recv_m > m) | po_m.recv_m.isna())].qty_ordered.sum()
            age = int(rng.gamma(3, 12)) + (60 if c.startswith("CMP-HDD") else 0)   # HDDs linger (E&O risk)
            inv_rows.append((m.end_time.date(), hub, c, int(on_hand), int(on_order), age))
inventory_snapshots = pd.DataFrame(inv_rows, columns=["snapshot_date", "hub_id", "component_id", "on_hand_qty", "on_order_qty", "avg_age_days"])

# ---------------------------------------------------------------- supplier invoices (AP)
inv_rows = []
closed = purchase_orders[purchase_orders.status == "Closed"]
for i, (po, g) in enumerate(closed.groupby("po_number")):
    s = g.supplier_id.iloc[0]
    terms = int(sup.loc[s, "payment_terms_days"])
    inv_date = pd.Timestamp(pd.to_datetime(g.received_date).max()) + pd.Timedelta(days=int(rng.integers(1, 10)))
    due = inv_date + pd.Timedelta(days=terms)
    amount = round(float((g.qty_received * g.unit_cost_usd).sum()), 2)
    if amount <= 0:
        continue
    behaviour = rng.random()
    if behaviour < 0.70:
        paid = due - pd.Timedelta(days=int(rng.integers(0, 5)))
    elif behaviour < 0.92:
        paid = due + pd.Timedelta(days=int(rng.gamma(2, 8)))
    else:
        paid = pd.NaT                                                   # disputed / unpaid
    if pd.notna(paid) and paid > END:
        paid = pd.NaT
    inv_rows.append((f"INV-{s[-3:]}-{i:06d}", s, po, inv_date.date(), due.date(),
                     paid.date() if pd.notna(paid) else None, amount, "USD"))
supplier_invoices = pd.DataFrame(inv_rows, columns=["invoice_id", "supplier_id", "po_number", "invoice_date",
                                                    "due_date", "paid_date", "amount_usd", "currency"])

# ---------------------------------------------------------------- GL journal + budget
gl_rows, jid = [], 0
def post(date, acct, cc, amount, source, ref, memo):
    global jid
    jid += 1
    gl_rows.append((f"JE-{jid:08d}", pd.Timestamp(date).date(), acct, cc, round(float(amount), 2), source, ref, memo))

# Receipts -> inventory / AP. Price variance vs standard -> PPV.
for _, p in closed.iterrows():
    if p.qty_received == 0:
        continue
    std_val = p.qty_received * std_cost[p.component_id]
    act_val = p.qty_received * p.unit_cost_usd
    post(p.received_date, "1400", "CC-1100", std_val, "PO Receipt", p.po_line_id, f"Receipt {p.component_id}")
    post(p.received_date, "5600", "CC-1300", act_val - std_val, "PO Receipt", p.po_line_id, "PPV vs standard")
    post(p.received_date, "2100", "CC-1100", -act_val, "PO Receipt", p.po_line_id, "AP accrual")
# Rack install -> capitalize (inventory relief at std) + monthly straight-line depreciation.
live = rack_deployments.dropna(subset=["installed_date"])
for _, r in live.iterrows():
    cc = region_cc[r.region_code]
    post(r.installed_date, "1500", cc, r.capex_usd, "Capitalization", r.rack_id, f"Rack in service {r.sku_id}")
    post(r.installed_date, "1400", "CC-1100", -r.capex_usd, "Capitalization", r.rack_id, "Inventory relief")
    monthly = r.capex_usd / r.useful_life_months
    m = pd.Period(r.installed_date, "M") + 1
    while m <= MONTHS[-1]:
        post(m.end_time.normalize(), "5100", cc, monthly, "Depreciation", r.rack_id, "Straight-line")
        post(m.end_time.normalize(), "1590", cc, -monthly, "Depreciation", r.rack_id, "Straight-line")
        m += 1
# Run-rate opex by region cost center, with seasonality on power.
opex_base = {"5200": 7_500_000, "5300": 3_800_000, "5400": 1_600_000, "5500": 900_000, "5800": 180_000}
for rc, cc in region_cc.items():
    w = float(regions.set_index("region_code").loc[rc, "demand_weight"])
    launched = pd.Timestamp(regions.set_index("region_code").loc[rc, "launched_date"])
    for mi, m in enumerate(MONTHS):
        if launched > m.end_time:
            continue
        for acct, base in opex_base.items():
            season = 1.0 + (0.12 * np.sin((m.month - 1) / 12 * 2 * np.pi - 1.2) if acct == "5200" else 0)
            amt = base * w * growth[mi] * season * rng.normal(1.0, 0.05)
            post(m.end_time.normalize(), acct, cc, amt, "Accrual", f"{cc}-{m}", f"{acct} monthly accrual")
# Global orgs: salaries + services.
for cc in ("CC-1100", "CC-1200", "CC-1300", "CC-3100", "CC-3200"):
    for m in MONTHS:
        post(m.end_time.normalize(), "5400", cc, 420_000 * rng.normal(1.0, 0.03), "Payroll", f"{cc}-{m}", "Salaries & benefits")
        post(m.end_time.normalize(), "5800", cc, 35_000 * rng.normal(1.0, 0.3), "Accrual", f"{cc}-{m}", "Consulting / services")
# E&O write-down on aged HDD inventory, quarterly.
for m in MONTHS:
    if m.month in (3, 6, 9, 12):
        post(m.end_time.normalize(), "5700", "CC-1100", rng.uniform(80_000, 350_000), "Adjustment", f"EO-{m}", "Excess & obsolete reserve")
        post(m.end_time.normalize(), "1400", "CC-1100", -gl_rows[-1][4], "Adjustment", f"EO-{m}", "Excess & obsolete reserve")
gl_journal = pd.DataFrame(gl_rows, columns=["journal_id", "posting_date", "account_id", "cost_center_id", "amount_usd",
                                            "source", "reference", "memo"])

# Budget: last year's run-rate shape with a planned growth rate, set before the year started.
actual_m = gl_journal.assign(fm=pd.to_datetime(gl_journal.posting_date).dt.to_period("M"))
actual_m = actual_m[actual_m.account_id.str.startswith("5")].groupby(["fm", "cost_center_id", "account_id"]).amount_usd.sum()
budget_rows = []
for (m, cc, acct), amt in actual_m.items():
    planned = amt * rng.normal(0.94 if acct in ("5100", "5200") else 1.02, 0.10)   # under-planned depreciation & power
    budget_rows.append((m.strftime("%Y-%m-01"), cc, acct, round(float(planned), 2)))
budget = pd.DataFrame(budget_rows, columns=["fiscal_month", "cost_center_id", "account_id", "budget_usd"])

# ---------------------------------------------------------------- write
tables = {
    "regions": regions.drop(columns="demand_weight"),
    "hubs": hubs,
    "suppliers": suppliers.drop(columns=["_otp", "_lead"]),
    "components": components,
    "server_skus": server_skus,
    "bom": bom,
    "purchase_orders": purchase_orders,
    "inventory_snapshots": inventory_snapshots,
    "capacity_forecast": capacity_forecast,
    "rack_deployments": rack_deployments.assign(**{c: rack_deployments[c].dt.date for c in ("shipped_date", "installed_date", "live_date")}),
    "supplier_invoices": supplier_invoices,
    "cost_centers": cost_centers,
    "gl_accounts": gl_accounts,
    "gl_journal": gl_journal,
    "budget": budget,
}
OUT_CSV.mkdir(parents=True, exist_ok=True)
for name, df in tables.items():
    (OUT_PQ / name).mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT_PQ / name / f"{name}.parquet", index=False)
    df.to_csv(OUT_CSV / f"{name}.csv", index=False)
    print(f"{name:22s} {len(df):>8,} rows")
