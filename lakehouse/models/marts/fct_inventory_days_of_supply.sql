-- Gold: month-end inventory vs trailing-3-month consumption. Days of supply and aging per hub/component.
with consumption as (
    -- Components consumed = racks built at the hub that month x BOM
    select
        r.requested_month      as snapshot_month,
        r.hub_id,
        b.component_id,
        sum(b.qty_per_unit * s.units_per_rack) as qty_consumed
    from {{ ref('stg_rack_deployments') }} r
    join {{ source('bronze', 'bom') }}         b using (sku_id)
    join {{ source('bronze', 'server_skus') }} s using (sku_id)
    group by 1, 2, 3
),
snap as (
    select
        date_trunc('month', snapshot_date)::date as snapshot_month,
        snapshot_date, hub_id, component_id, on_hand_qty, on_order_qty, avg_age_days
    from {{ source('bronze', 'inventory_snapshots') }}
),
joined as (
    select
        snap.*,
        c.component_name,
        c.category                 as component_category,
        c.standard_cost_usd,
        coalesce(consumption.qty_consumed, 0) as qty_consumed,
        avg(coalesce(consumption.qty_consumed, 0)) over (
            partition by snap.hub_id, snap.component_id
            order by snap.snapshot_month rows between 2 preceding and current row
        ) as avg_monthly_consumption_3m
    from snap
    join {{ source('bronze', 'components') }} c using (component_id)
    left join consumption using (snapshot_month, hub_id, component_id)
)
select
    snapshot_date,
    hub_id,
    component_id,
    component_name,
    component_category,
    on_hand_qty,
    on_order_qty,
    qty_consumed,
    round(avg_monthly_consumption_3m, 1)                                   as avg_monthly_consumption_3m,
    round(on_hand_qty / nullif(avg_monthly_consumption_3m / 30.0, 0), 0)   as days_of_supply,
    avg_age_days,
    round(on_hand_qty * standard_cost_usd, 2)                              as on_hand_value_usd,
    avg_age_days > 180                                                     as is_eo_risk
from joined
