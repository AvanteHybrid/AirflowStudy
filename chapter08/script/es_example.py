"""
# Documentation of pageview format: https://wikitech.wikimedia.org/wiki/Analytics/Data_Lake/Traffic/Pageviews
# """

import airflow.utils.dates
from airflow import DAG
from airflow.operators.dummy import DummyOperator
from es_hook_operator.es_hook_operator import ElasticOperator

dag = DAG(
    dag_id="es_test",
    start_date=airflow.utils.dates.days_ago(1),
    schedule_interval="@hourly",
    template_searchpath="/tmp",
    max_active_runs=1,
)

es_exam = ElasticOperator(
    task_id='es_exam',
    conn_id='perception-test-es',
    end_date='{{next_ds}}',
    dag=dag
)

dummy = DummyOperator(task_id='dummy', dag=dag)

es_exam >> dummy