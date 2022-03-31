# How to use `execution_date_fn`

책에서 `ExternalTaskSensor` 소개를 하면서 다른 DAG의 Task를 검색할 시 기본적으로 실행 날짜가 동일해야한다고 말하고 있다.
하지만 스케줄 간격이 다른 DAG들이 있을 수 있으므로 이런 경우에 다른 DAG 검색을 위한 offset을 설정할 수 있다고 한다.
offset은 `execution_delta` 값을 지정해주어 동작하게 할 수도 있고 `execution_date_fn`를 지정해줄 수 있는데 후자에 대한 예시를 살펴보기로 한다.

[Official docs](https://airflow.apache.org/docs/apache-airflow/1.10.12/_api/airflow/sensors/external_task_sensor/index.html#airflow.sensors.external_task_sensor.ExternalTaskSensor)에 따르면, `execution_date_fn`에는 현재 실행 중인 DAG의 execution date를 인자로 받아서 찾고자 하는 execution date를 return하면 된다고 나와있다.
(NOTE: `execution_date_fn`과 `execution_delta` 중 하나만 값을 설정할 수 있다.)

책에서 나온대로, DAG1은 하루에 한 번 (@daily), DAG2는 5시간마다 (0 */5 * * *) 실행된다고 치자.
이런 경우 `execution_delta` 값만으로는 DAG1의 execution_date를 찾기 힘들다.
DAG2에서는 DAG1을 찾을 수 있도록 `execution_date_fn`이 설정 되어야 한다.

```python
# WARNING: Not tested thus error-prone.

def _execution_dt_fn(execution_date, **kwargs):
    # retrieve hour field from current
    execution_hour = execution_date.strftime('%H')
    # Since DAG1 is executed daily every midnight, we can calculate the time
    # by subtracting hour retrieved from current execution date.
    execution_dt_derived = execution_date - timedelta(hours=execution_hour)
    
    return execution_dt_derived


// ... 생략

dag1 = DAG(dag_id="dag1", schedule_interval="@daily")
dag2 = DAG(dag_id="dag2", schedule_interval="* */5 * * *")

DummyOperator(task_id="etl", dag=dag1)

ExternalTaskSensor(
    task_id="wait_for_etl",
    external_dag_id="dag1",
    external_task_id="etl",
    execution_date_fn=_execution_dt_fn,
    dag=dag2
)
```