-- Gold: forecast accuracy. 6-month plan vs 1-month commit vs racks actually requested.
with actual as (
    select requested_month as forecast_month, region_code, sku_family, count(*) as actual_racks
    from {{ ref('stg_rack_deployments') }}
    group by 1, 2, 3
),
fc as (
    select
        forecast_month::date as forecast_month,
        region_code,
        sku_family,
        max(case when forecast_version = 'P6M' then forecast_racks end) as plan_6m_racks,
        max(case when forecast_version = 'P1M' then forecast_racks end) as commit_1m_racks
    from {{ source('bronze', 'capacity_forecast') }}
    group by 1, 2, 3
)
select
    fc.forecast_month,
    fc.region_code,
    fc.sku_family,
    fc.plan_6m_racks,
    fc.commit_1m_racks,
    coalesce(actual.actual_racks, 0)                                    as actual_racks,
    coalesce(actual.actual_racks, 0) - fc.plan_6m_racks                  as variance_vs_plan,
    coalesce(actual.actual_racks, 0) - fc.commit_1m_racks                as variance_vs_commit,
    round(100.0 * abs(coalesce(actual.actual_racks, 0) - fc.plan_6m_racks) / nullif(fc.plan_6m_racks, 0), 1)   as plan_abs_pct_error,
    round(100.0 * abs(coalesce(actual.actual_racks, 0) - fc.commit_1m_racks) / nullif(fc.commit_1m_racks, 0), 1) as commit_abs_pct_error
from fc
left join actual using (forecast_month, region_code, sku_family)
