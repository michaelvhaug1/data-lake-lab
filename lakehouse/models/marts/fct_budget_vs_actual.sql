-- Gold: opex actuals vs budget by cost center, account and month. The monthly close variance report.
with actual as (
    select fiscal_month, cost_center_id, account_id, sum(amount_usd) as actual_usd
    from {{ ref('stg_gl_journal') }}
    where account_type = 'Opex'
    group by 1, 2, 3
),
bud as (
    select fiscal_month::date as fiscal_month, cost_center_id, account_id, sum(budget_usd) as budget_usd
    from {{ source('bronze', 'budget') }}
    group by 1, 2, 3
)
select
    coalesce(actual.fiscal_month, bud.fiscal_month)       as fiscal_month,
    coalesce(actual.cost_center_id, bud.cost_center_id)   as cost_center_id,
    cc.cost_center_name,
    cc.org,
    cc.region_code,
    coalesce(actual.account_id, bud.account_id)           as account_id,
    a.account_name,
    round(coalesce(actual.actual_usd, 0), 2)              as actual_usd,
    round(coalesce(bud.budget_usd, 0), 2)                 as budget_usd,
    round(coalesce(actual.actual_usd, 0) - coalesce(bud.budget_usd, 0), 2) as variance_usd,
    round(100.0 * (coalesce(actual.actual_usd, 0) - coalesce(bud.budget_usd, 0)) / nullif(bud.budget_usd, 0), 1) as variance_pct
from actual
full outer join bud using (fiscal_month, cost_center_id, account_id)
join {{ source('bronze', 'cost_centers') }} cc on cc.cost_center_id = coalesce(actual.cost_center_id, bud.cost_center_id)
join {{ source('bronze', 'gl_accounts') }}  a  on a.account_id      = coalesce(actual.account_id, bud.account_id)
