update exchangerate
set is_actual = '0'
where (from_unit, to_unit, "date") in (
    {% for record in task_instance.xcom_pull(task_ids="get_exchange_rate") -%}
    (
        '{{ record["from_unit"] }}',
        '{{ record["to_unit"] }}',
        '{{ record["date"] }}'
    ){% if not loop.last %},{% endif %}
    {%- endfor %}
);