-- Gold: racks placed in service, capitalized cost and run-rate depreciation by region and month.
select
    date_trunc('month', installed_date)::date   as in_service_month,
    region_code,
    region_name,
    sku_family,
    count(*)                                    as racks_in_service,
    round(sum(capex_usd), 2)                    as capex_usd,
    round(sum(monthly_depreciation_usd), 2)     as added_monthly_depreciation_usd,
    round(avg(request_to_live_days), 1)         as avg_request_to_live_days
from {{ ref('stg_rack_deployments') }}
where installed_date is not null
group by 1, 2, 3, 4
