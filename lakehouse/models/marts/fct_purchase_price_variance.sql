-- Gold: purchase price variance vs standard cost, by component category and month.
-- Positive = paying more than standard (GPU allocation premium, DRAM cycle).
select
    date_trunc('month', received_date)::date            as received_month,
    component_category,
    component_id,
    component_name,
    sum(qty_received)                                   as qty_received,
    round(sum(qty_received * standard_cost_usd), 2)     as standard_value_usd,
    round(sum(received_value_usd), 2)                   as actual_value_usd,
    round(sum(ppv_usd), 2)                              as ppv_usd,
    round(100.0 * sum(ppv_usd) / nullif(sum(qty_received * standard_cost_usd), 0), 2) as ppv_pct
from {{ ref('stg_purchase_orders') }}
where status = 'Closed' and qty_received > 0
group by 1, 2, 3, 4
