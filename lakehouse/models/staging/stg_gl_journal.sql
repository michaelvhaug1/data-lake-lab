-- Silver: journal lines with account and cost-center attributes attached.
select
    j.journal_id,
    j.posting_date,
    date_trunc('month', j.posting_date)::date   as fiscal_month,
    j.account_id,
    a.account_name,
    a.account_type,
    j.cost_center_id,
    cc.cost_center_name,
    cc.org,
    cc.region_code,
    j.amount_usd,
    j.source,
    j.reference,
    j.memo
from {{ source('bronze', 'gl_journal') }} j
join {{ source('bronze', 'gl_accounts') }}  a  using (account_id)
join {{ source('bronze', 'cost_centers') }} cc using (cost_center_id)
