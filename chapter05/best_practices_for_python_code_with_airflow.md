## Airflow로 Python code 쓸 때 주의 점

airflow documentation을 보다가 흥미로운 내용을 발견했다.
[Top level Python Code](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html?highlight=trigger#top-level-python-code)

### 특히 외부 package의 import를 code top level에 하지 말것!

document에서 말하길 package를 import 할 때 code의 top level에 하지 말것을 요청하고 있다. 대신 각 task function 내에서 import를 할 것을 요청하고 있다.
#### 이유
 - top level import의 경우 DAG의 loading time이 증가한다.
 - top level import의 경우 overhead가 커진다.

아래의 간단한 코드조차 top level import가 local import로 바뀌었다는 이유로 몇 초 정도 DAG 로딩에 차이가 나게 된다고 한다.

 - 나쁜 예!
    ```python
    import pendulum

    from airflow import DAG
    from airflow.operators.python import PythonOperator

    import numpy as np  # <-- THIS IS A VERY BAD IDEA! DON'T DO THAT!

    with DAG(
        dag_id="example_python_operator",
        schedule_interval=None,
        start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
        catchup=False,
        tags=["example"],
    ) as dag:

        def print_array():
            """Print Numpy array."""
            a = np.arange(15).reshape(3, 5)
            print(a)
            return a

        run_this = PythonOperator(
            task_id="print_the_context",
            python_callable=print_array,
        )
    ```

 - 좋은 예!
    ```python
    import pendulum

    from airflow import DAG
    from airflow.operators.python import PythonOperator

    with DAG(
        dag_id="example_python_operator",
        schedule_interval=None,
        start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
        catchup=False,
        tags=["example"],
    ) as dag:

        def print_array():
            """Print Numpy array."""
            import numpy as np  # <- THIS IS HOW NUMPY SHOULD BE IMPORTED IN THIS CASE

            a = np.arange(15).reshape(3, 5)
            print(a)
            return a

        run_this = PythonOperator(
            task_id="print_the_context",
            python_callable=print_array,
        )
    ```

### top level code 작성하지 않기!
아래의 `dont_do_this_at_home` 과 같은 함수는 Top level에 작성되었다. Airflow는 DAG안에 기술되지 않은 Top level의 code를 읽어오는 데 있어서 parsing speed가 느리도록(DAG 안을 훨씬 빠르게 parsing하도록) 디자인 되어 있기 때문에, top level에 코드를 쓰지 않는 것이 좋다.
```python
import pendulum

from airflow import DAG
from airflow.operators.python import PythonOperator

def dont_do_this_at_home(param: str):
    print(param)
    return "I am not happy"

with DAG(
    dag_id="example_python_operator",
    schedule_interval=None,
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    tags=["example"],
) as dag:
```

### DAG 복잡성을 줄여라!
 - 가능하면 DAG 로드 속를 빠르게 하라: 스케쥴러의 performance에 매우 큰 영향! DAG loader test로 로딩 타임 체크 할것!
 - DAG의 구조를 최대한 간단하게 만들 것.
 - 한 파일 당 DAG를 최대한 줄일 것! Airflow 2는 한 파일에 여러 DAG가 있을 때도 최대한 성능을 보장하도록 설계되었지만, 여전히 여러 파일에 DAG가 나뉘어져 있을 때 보다는 덜 효율적으로 작동한다!
