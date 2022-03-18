## Taskflow API 작동 방식 살펴보기.

이전 챕터의 [자료](../chapter03/taskflow_with_automatic_dependencies.py)에는 아래와 같은 코드가 소개되는데, 실제로 어떻게 작동하는 지 궁금했다.
chapter04와 약간의 관련이 있을 수도 없을 수도 있지만, 일단 한 번 살펴보고자 한다.

```python
@task()
def extract():
    data_string = '{"1001": 301.27, "1002": 433.21, "1003": 502.22}'
    order_data_dict = json.loads(data_string)
    return order_data_dict

@task(multiple_outputs=True)
def transform(order_data_dict: dict):
    total_order_value = 0
    for value in order_data_dict.values():
        total_order_value += value
    return {"total_order_value": total_order_value}

order_data = extract()
order_summary = transform(order_data)
```

### task()로 decorated 된 함수는 어떻게 동작할까?
위 예제의 `order_data = extract()` 여기서 extract()는 어떻게 동작하는 것일까?
airflow 소스코드의 현재 메인 브랜치를 기준으로 살펴보았다. 릴리즈 버전과는 코드 구조가 많이 다른 것 같긴 한데, 동작하는 방식은 비슷한 것 같다.
코드를 타고 타고 들어가다보면 클래스 형태로 구현된 [TaskDecorator](https://github.com/apache/airflow/blob/main/airflow/decorators/base.py#L221)를 만날 수 있다.
```python
class _TaskDecorator(Generic[Function, OperatorSubclass]):
    ...

    def __call__(self, *args, **kwargs) -> XComArg:
        op = self.operator_class(
            python_callable=self.function,
            op_args=args,
            op_kwargs=kwargs,
            multiple_outputs=self.multiple_outputs,
            **self.kwargs,
        )
        if self.function.__doc__:
            op.doc_md = self.function.__doc__
        return XComArg(op)
```
  - Operator를 생성하고 python_callable로 decorated function을 넘겨준다.
    - operator_class로는 PythonOperator의 variant들이 올 것 같다.
  - XComArg 클래스 인스턴스를 리턴한다.


### task()로 decorated 된 함수가 반환한 값의 정체는?
위 예제 중 ```order_data = extract()``` 에서 order_data는 어떤 정확히 어느 타입의 변수일까? 앞서 살펴본대로 task() 로 decorated된 함수는 [XComArg](https://airflow.apache.org/docs/apache-airflow/stable/_api/airflow/models/xcom_arg/index.html#airflow.models.xcom_arg.XComArg) 클래스 인스턴스를 리턴하는데, 이전의 operator가 Xcom에 푸시한 값을 나타낸다.

```python
class XComArg(DependencyMixin):
    def __init__(self, operator: "Operator", key: str = XCOM_RETURN_KEY):
        self.operator = operator
        self.key = key

    ...

    def resolve(self, context: Context) -> Any:
        ...
        resolved_value = context['ti'].xcom_pull(task_ids=[self.operator.task_id], key=str(self.key))
        ...

```
 - init 시에 operator와 key를 받고, key의 디폴트 값은 "return_value"다.
   - 아마 operator에서 execute 메소드의 return 값을 Xcom에 푸시할 때 해당 key를 사용하는 모양이다.
 - resolve 메소드를 통해서 해당 operator, key에 해당되는 값을 XCom에서 받아온다.

### 이전 Operator가 XCom에 푸시한 값은 언제 pull 될까
위 예제 마지막 줄 `order_summary = transform(order_data)` 에서 transform 함수는 언제 XCom에서 값을 받아올까. 즉, order_data.resolve()는 언제 실행이 될까.
- 앞서 TaskDecorator에서 살펴봤듯, 일단 받은 argument들은 모조리 operator의 op_args와 op_kwargs로 전달된다.
- 해당 task가 실행되기 전에 op_args와 op_kwargs들을 렌더링하는 과정에서 XComArg의 resolve 메소드가 실행된다.
  아래는 [AbstractOperator.render_template](https://github.com/apache/airflow/blob/4a1503b39b0aaf50940c29ac886c6eeda35a79ff/airflow/models/abstractoperator.py#L331)의 일부다.
    ```python
    def render_template(
            self,
            ...
        ) -> Any:
            ...
            if isinstance(value, (DagParam, XComArg)):
                return value.resolve(context)
    ```

### 같은 코드를 Airflow 1.x 버전에서 작성한다면..
위 예제를 기존의 방식으로 작성한다면 아래와 같이 작성할 수 있을 것이다. [튜토리얼](https://airflow.apache.org/docs/apache-airflow/stable/tutorial_taskflow_api.html#but-how) 코드를 약간 변형했다.
```python
with DAG(
    ...
):
    def _extract():
        data_string = '{"1001": 301.27, "1002": 433.21, "1003": 502.22}'
        order_data_dict = json.loads(data_string)
        return order_data_dict

    def _transform(**context):
        ti: TaskInstance = context['ti']
        order_data_dict = ti.xcom_pull(task_ids='extract')
        total_order_value = 0
        for value in order_data_dict.values():
            total_order_value += value
        return {"total_order_value": total_order_value}

    extract = PythonOperator(
        task_id='extract',
        python_callable=_extract,
    )

    transform = PythonOperator(
        task_id='transform',
        python_callable=_transform,
    )

    extract >> transform
```
 - context의 TaskInstance를 불러와 xcom_pull 메소드를 실행해 앞의 task에서 push한 return value를 받아온다.
 - TaskFlow API로 작성했을때와 비교해서, task간 값이 전달되고 있다는 사실을 python_callable 함수들을 살펴봐야 알 수 있다는 단점이 있다.

### 끝내며..
TaskFlow API는 확실히 사용자는 모르게 뭔가 많은 일을 잘 숨겨놓아서, 사용자 입장에서 뒷단 일을 잘 몰라도 직관적이고 pythonic한 코드 작성이 가능한 것 같다. 한편으로 이런 고수준의 API의 한계점들이 있을텐데, 책 5장에서는 아래와 같은 점을 설명한다.
 - 일단 현재로서는 PythonOperator에 대해서만 지원한다.
 - 그러다보니 TaskFlow API를 사용하면서 다른 operator를 함께 사용할 경우 코드 스타일이 뒤섞여 task간 dependency가 한눈에 안들어올 수도 있다. ([예제](https://github.com/BasPH/data-pipelines-with-apache-airflow/blob/master/chapter05/dags/13_taskflow_full.py))
 - 또한 XCom 사용이 강제되는데, 이 때문에 변수 전달에 사이즈, 타입 등의 여러 제약이 생긴다.
