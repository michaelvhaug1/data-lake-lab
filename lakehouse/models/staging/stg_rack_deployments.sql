-- Silver: racks with cycle-time measures from request to live.
select
    r.rack_id,
    r.region_code,
    rg.region_name,
    r.hub_id,
    r.sku_id,
    r.sku_family,
    r.requested_date,
    r.shipped_date,
    r.installed_date,
    r.live_date,
    date_trunc('month', r.requested_date)::date         as requested_month,
    date_trunc('month', r.live_date)::date              as live_month,
    datediff('day', r.requested_date, r.live_date)     as request_to_live_days,
    datediff('day', r.shipped_date, r.installed_date)  as ship_to_install_days,
    r.capex_usd,
    r.useful_life_months,
    r.capex_usd / r.useful_life_months                  as monthly_depreciation_usd
from {{ source('bronze', 'rack_deployments') }} r
join {{ source('bronze', 'regions') }} rg using (region_code)
