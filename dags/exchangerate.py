import datetime
import os

import airflow
from airflow import DAG
from airflow.operators.http_operator import SimpleHttpOperator
from airflow.operators.postgres_operator import PostgresOperator

import requests

PATH, FILENAME = os.path.split(os.path.abspath(__file__))

# DAG settings for actual exchange rates extraction
BASE_DAG_ID = FILENAME.replace(".py", "")
BASE_SCHEDULE = "0 */3 * * *"
BASE_START_DATE = airflow.utils.dates.days_ago(1)

# DAG settings for historical exchange rates extraction
HIST_SCHEDULE = "30 0 * * *"
HIST_START_DATE = datetime.datetime(2022, 1, 1)

default_args = {
    'owner': 'Evgenii Panteleev',
    'retries': 2,
    'retry_delay': datetime.timedelta(minutes=15)
}


def sql_path(name: str) -> str:
    """ Returns sql template path by name """
    return os.path.join("sql", f"{name}.sql")


def check_response(
    response: requests.Response
) -> bool:
    """ Returns True if response is ok else False """
    if not response.ok:
        return False

    data = response.json()
    return data.get("success", False)


def transform_response(
    response: requests.Response
) -> dict:
    """ Returns transformed response from api.exchangerate.host """
    data = response.json()
    return [
        {
            "from_unit": data["base"],
            "to_unit": unit,
            "date": data["date"],
            "rate": rate
        }
        for unit, rate in data["rates"].items()
    ]


def create_table_task_factory(dag: DAG) -> PostgresOperator:
    """ Returns exchange rates log table creation operator """
    return PostgresOperator(
        task_id="create_table",
        postgres_conn_id="postgres_default",
        sql=sql_path("create"),
        dag=dag
    )


def get_exchange_rate_task_factory(
    dag: DAG,
    hist: bool = False
) -> SimpleHttpOperator:
    """ Returns exchange rates request operator """
    return SimpleHttpOperator(
        task_id="get_exchange_rate",
        method="GET",
        http_conn_id="exchangerate",
        endpoint=(
            "{{ execution_date | ds }}"
            if hist
            else "latest"
        ),
        do_xcom_push=True,
        data={
            "base": "{{ var.value.get('exchangerate.base', 'BTC') }}",
            "symbols": "{{ var.value.get('exchangerate.symbols', 'USD') }}"
        },
        headers={
            "accept": "application/json",
            "Content-Type": "application/json"
        },
        response_check=check_response,
        response_filter=transform_response,
        dag=dag
    )


def update_is_actual_task_factory(dag: DAG) -> PostgresOperator:
    """ Returns operator for is_actual flag updates """
    return PostgresOperator(
        task_id="update_is_actual",
        postgres_conn_id="postgres_default",
        sql=sql_path("update"),
        dag=dag
    )


def insert_exchange_rate_task_factory(dag: DAG) -> PostgresOperator:
    """ Returns operator for inserting exchange rate """
    return PostgresOperator(
        task_id="insert_exchange_rate",
        postgres_conn_id="postgres_default",
        sql=sql_path("insert"),
        dag=dag
    )


def dag_factory(hist: bool = False):
    """ Returns airflow DAG object """
    args = dict(
        **default_args,
        start_date=HIST_START_DATE if hist else BASE_START_DATE
    )

    return DAG(
        dag_id=BASE_DAG_ID + "_hist" if hist else BASE_DAG_ID,
        max_active_runs=1,
        schedule_interval=HIST_SCHEDULE if hist else BASE_SCHEDULE,
        catchup=hist,
        default_args=args
    )


for hist in (True, False):
    dag = dag_factory(hist)

    create_table = create_table_task_factory(dag)
    get_exchange_rate = get_exchange_rate_task_factory(dag, hist)
    update_is_actual = update_is_actual_task_factory(dag)
    insert_exchange_rate = insert_exchange_rate_task_factory(dag)

    create_table \
        >> get_exchange_rate \
        >> update_is_actual \
        >> insert_exchange_rate

    globals()[dag.dag_id] = dag
