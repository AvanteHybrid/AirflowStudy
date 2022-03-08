import datetime
import airflow
from airflow.decorators import dag, task
from airflow.operators.python import get_current_context


@dag(
    schedule_interval='0 0 * * FRI,SUN',
    start_date=airflow.utils.dates.days_ago(30),
    catchup=True,
    tags=['example'],
    end_date=datetime.datetime(year=2022, month=3, day=20)
)
def taskflow_without_dependencies():
    @task
    def first_task(next_ds=None):
        print(next_ds)

    @task
    def second_task():
        pass

    # There is no clear evidence that they are related by parameters
    # Thus, Taskflow API does not set any dependencies
    a = first_task()
    b = second_task()

    # However, we can set dependencies just like using old style operators as below
    a >> b

test = taskflow_without_dependencies()