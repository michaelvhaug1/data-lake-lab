{# Two generic tests normally taken from dbt_utils, written inline so the project has no package dependency. #}

{% test dbt_utils_free_accepted_range(model, column_name, min_value=none, max_value=none) %}
select {{ column_name }}
from {{ model }}
where {{ column_name }} is not null
  and (
    {% if min_value is not none %}{{ column_name }} < {{ min_value }}{% else %}false{% endif %}
    or
    {% if max_value is not none %}{{ column_name }} > {{ max_value }}{% else %}false{% endif %}
  )
{% endtest %}

{% test dbt_utils_free_unique_combination(model, combination) %}
select {{ combination | join(', ') }}, count(*) as n
from {{ model }}
group by {{ combination | join(', ') }}
having count(*) > 1
{% endtest %}
