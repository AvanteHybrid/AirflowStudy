import datetime
import airflow
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator, get_current_context  # to load context


def next_ds_parameter_python(next_ds=None):
    print(next_ds)


def next_ds_kwargs_python(**kwargs):
    next_ds = kwargs.get('next_ds')
    print(next_ds)


def next_ds_python():
    # does not work. The result is "{{ds}}" but not the date format we wanted.
    print("{{ds}}")
    context = get_current_context()
    print(f"context: {context['next_ds']}")
    # filter fails
    # print(f"context_with_new next_ds: {context['data_interval_end | ds']}")

    # without filter, successful
    print(f"context_with_new next_ds: {context['data_interval_end']}")


dag = DAG(
    dag_id="context_testing",  # name of the DAG
    start_date=airflow.utils.dates.days_ago(14),  # The date of first run
    schedule_interval='@daily',  # DAG running interval
)


next_ds_bash = BashOperator(
    task_id="next_ds_bash",  # name of the task
    # below does not work because no context was found since this is python operator's module.
    # bash_command="echo {{next_ds}}" + f"{get_current_context()['next_ds']}", #
    bash_command="echo {{next_ds}}",
    dag=dag
)

next_ds_parameter_python = PythonOperator(
    task_id='next_ds_parameter_python',
    python_callable=next_ds_parameter_python,
    dag=dag
)
next_ds_kwargs_python = PythonOperator(
    task_id='next_ds_kwargs_python',
    python_callable=next_ds_kwargs_python,
    dag=dag
)
next_ds_python = PythonOperator(
    task_id='next_ds_python',
    python_callable=next_ds_python,
    dag=dag
)

next_ds_bash >> next_ds_parameter_python >> next_ds_kwargs_python >> next_ds_python
