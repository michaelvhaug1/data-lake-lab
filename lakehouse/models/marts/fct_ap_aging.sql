-- Gold: accounts payable aging as of the latest invoice date in the data, by supplier.
with as_of as (
    select max(invoice_date) as as_of_date from {{ source('bronze', 'supplier_invoices') }}
),
open_inv as (
    select
        i.*,
        s.supplier_name,
        s.payment_terms_days,
        datediff('day', i.due_date, as_of.as_of_date) as days_past_due
    from {{ source('bronze', 'supplier_invoices') }} i
    join {{ source('bronze', 'suppliers') }} s using (supplier_id)
    cross join as_of
    where i.paid_date is null
)
select
    (select as_of_date from as_of)                                           as as_of_date,
    supplier_id,
    supplier_name,
    payment_terms_days,
    count(*)                                                                 as open_invoices,
    round(sum(amount_usd), 2)                                                as open_usd,
    round(sum(case when days_past_due <= 0  then amount_usd else 0 end), 2)  as current_usd,
    round(sum(case when days_past_due between 1  and 30 then amount_usd else 0 end), 2) as past_due_1_30_usd,
    round(sum(case when days_past_due between 31 and 60 then amount_usd else 0 end), 2) as past_due_31_60_usd,
    round(sum(case when days_past_due between 61 and 90 then amount_usd else 0 end), 2) as past_due_61_90_usd,
    round(sum(case when days_past_due > 90  then amount_usd else 0 end), 2)  as past_due_over_90_usd
from open_inv
group by 1, 2, 3, 4
