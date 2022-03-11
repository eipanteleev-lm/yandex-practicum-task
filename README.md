# yandex-practicum-task

Repository for Yandex Practicum test task

## How to run?

За основу был взят базовый образ Airflow и docker-compose.yml из официальной [документации](https://airflow.apache.org/docs/apache-airflow/stable/start/docker.html). Развертывание нужно производить в соответствии с представленной там инструкцией.

В случае запуска с Linux/Mac os сначала нужно проделать следующую махинацию:

```sh
echo -e "AIRFLOW_UID=$(id -u)" > .env
```

Чтобы поднять Airflow нужно последовательно запустить следующие команды:

```sh
docker-compose up airflow-init
docker-compose up -d
```

## What is done?

Реализованы два DAGа `exchangerate` и `exchangerate_hist`:
 - **exchangerate** раз в 3 часа извлекает данные по текущему курсу указанной валютной пары с [exchangerate.host](https://exchangerate.host/#/) и складывает их в таблицу exchangerate в Postgres (для простоты использовалась БД с метаданными airflow, после развертывания будет доступна на порту 5432). Таблица имеет следующую структуру:
  ```sql
  create table if not exists exchangerate (
      from_unit text,  -- Валюта, из которой идет конвертация
      to_unit text,  -- Валюта, в которую идет конвертация
      "date" date,  -- Дата, на которую актуален курс (отдается exchangerate.host)
      rate numeric,  -- Курс
      created_dttm timestamptz default now(),  -- Дата и время создания записи в БД
      is_actual character(1) default 1  -- Признак последней записи
  );
  ```
 - **exchangerate_hist** - добывает исторические данные по курсу с 2022-01-01 и складывает их в ту же таблицу exchangerate.

Результат работы дагов можно увидеть в таблице exchangerate в БД с метаданными Airflow (connecion_id - postgres_default).

Параметры подключения:

```
  host: localhost  
  port: 5432  
  db: airflow  
  user: airflow  
  password: airflow  
```

С помощью Variables `exchangerate.base` и `exchangerate.symbols` можно регулировать список валют, курс которых нужно выгрузить.
 - **exchangerate.base** - строка, валюта, из которой идет конвертация, по умолчанию BTC;
 - **exchangerate.symbols** - строка, валюты, в которые идет конвертация, разделенные запятыми, по умолчанию USD;

Соединения со всеми источниками заведены через Connections на уровне переменных среды в docker-compose.yml, так что вручную заводить их не нужно.
