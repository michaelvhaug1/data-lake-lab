-- Silver: PO lines with supplier attributes and the OTIF flags every supply-chain review runs on.
select
    p.po_line_id,
    p.po_number,
    p.supplier_id,
    s.supplier_name,
    s.category                                             as supplier_category,
    s.strategic_flag,
    p.component_id,
    c.component_name,
    c.category                                             as component_category,
    p.hub_id,
    p.order_date,
    p.promised_date,
    p.received_date,
    p.qty_ordered,
    p.qty_received,
    p.unit_cost_usd,
    c.standard_cost_usd,
    p.status,
    date_trunc('month', p.promised_date)::date             as promised_month,
    p.received_date is not null
        and p.received_date <= p.promised_date             as is_on_time,
    p.qty_received >= p.qty_ordered                        as is_in_full,
    p.received_date is not null
        and p.received_date <= p.promised_date
        and p.qty_received >= p.qty_ordered                as is_otif,
    datediff('day', p.promised_date, p.received_date)     as days_late,
    p.qty_received * p.unit_cost_usd                       as received_value_usd,
    p.qty_received * (p.unit_cost_usd - c.standard_cost_usd) as ppv_usd
from {{ source('bronze', 'purchase_orders') }} p
join {{ source('bronze', 'suppliers') }}  s using (supplier_id)
join {{ source('bronze', 'components') }} c using (component_id)
