create table if not exists exchangerate (
    from_unit text,
    to_unit text,
    "date" date,
    rate numeric,
    created_dttm timestamptz default now(),
    is_actual character(1) default 1
);

create index if not exists idx_exchangerate on exchangerate (
    from_unit,
    to_unit,
    "date"
);