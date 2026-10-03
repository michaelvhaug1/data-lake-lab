-- Gold: supplier on-time / in-full performance by month. The supplier scorecard.
select
    promised_month,
    supplier_id,
    supplier_name,
    supplier_category,
    strategic_flag,
    count(*)                                            as po_lines,
    sum(qty_ordered)                                    as qty_ordered,
    sum(qty_received)                                   as qty_received,
    round(100.0 * avg(is_on_time::int), 1)              as on_time_pct,
    round(100.0 * avg(is_in_full::int), 1)              as in_full_pct,
    round(100.0 * avg(is_otif::int), 1)                 as otif_pct,
    round(avg(case when not is_on_time then days_late end), 1) as avg_days_late_when_late,
    round(sum(received_value_usd), 2)                   as received_value_usd
from {{ ref('stg_purchase_orders') }}
where status = 'Closed'
group by 1, 2, 3, 4, 5
