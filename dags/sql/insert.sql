insert into exchangerate (
    from_unit,
    to_unit,
    "date",
    rate
)
values {% for record in task_instance.xcom_pull(task_ids="get_exchange_rate") -%}
    (
        '{{ record["from_unit"] }}',
        '{{ record["to_unit"] }}',
        '{{ record["date"] }}',
        '{{ record["rate"] }}'
    ){% if not loop.last %},{% endif %}
{%- endfor %};