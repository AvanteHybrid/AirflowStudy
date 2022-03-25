## Branch Operators 모음

챕터5 앞부분은 BranchPythonOperator를 통한 branching 방법에 대해 소개한다.
airflow 자체적으로 제공하는 BranchOperator가 몇 가지 더 있는 것 같아 정리해본다.

### BranchDateTimeOperator
`airflow.operators.datetime.BranchDateTimeOperator` 를 통해서 특정 datetime range 안에 있는 경우와
그렇지 않은 경우에 대해 branching이 가능하다. [문서](https://airflow.apache.org/docs/apache-airflow/stable/howto/operator/datetime.html)에 소개된 예제는 아래와 같다.

```python
# source: https://airflow.apache.org/docs/apache-airflow/stable/howto/operator/datetime.html

dummy_task_1 = DummyOperator(task_id='date_in_range', dag=dag)
dummy_task_2 = DummyOperator(task_id='date_outside_range', dag=dag)

cond1 = BranchDateTimeOperator(
    task_id='datetime_branch',
    follow_task_ids_if_true=['date_in_range'],
    follow_task_ids_if_false=['date_outside_range'],
    target_upper=pendulum.datetime(2020, 10, 10, 15, 0, 0),
    target_lower=pendulum.datetime(2020, 10, 10, 14, 0, 0),
    dag=dag,
)

# Run dummy_task_1 if cond1 executes between 2020-10-10 14:00:00 and 2020-10-10 15:00:00
cond1 >> [dummy_task_1, dummy_task_2]

cond2 = BranchDateTimeOperator(
    task_id='datetime_branch',
    follow_task_ids_if_true=['date_in_range'],
    follow_task_ids_if_false=['date_outside_range'],
    target_upper=pendulum.time(0, 0, 0),
    target_lower=pendulum.time(15, 0, 0),
    dag=dag,
)

# Since target_lower happens after target_upper, target_upper will be moved to the following day
# Run dummy_task_1 if cond2 executes between 15:00:00, and 00:00:00 of the following day
cond2 >> [dummy_task_1, dummy_task_2]
```
 - *target_lower*와 *target_upper*를 통해 실행 시간의 range를 설정할 수 있다.
   - pendulum.datetime과 pendulum.time 모두 사용 가능하다.
 - *follow_task_ids_if_true*와 *follow_task_ids_if_false*를 통해 해당 range 안에 있을 때와 그렇지 않을 경우
   실행할 task id를 넘겨준다.


### BranchDayOfWeekOperator
`airflow.operators.weekday.BranchDayOfWeekOperator`을 통해 요일에 따른 브랜칭도 가능한 것 같다.
아래는 [문서](https://airflow.apache.org/docs/apache-airflow/stable/howto/operator/weekday.html)에
소개된 예제이다.

```python
# source: https://airflow.apache.org/docs/apache-airflow/stable/howto/operator/weekday.html
dummy_task_1 = DummyOperator(task_id='branch_true', dag=dag)
dummy_task_2 = DummyOperator(task_id='branch_false', dag=dag)

branch = BranchDayOfWeekOperator(
    task_id="make_choice",
    follow_task_ids_if_true="branch_true",
    follow_task_ids_if_false="branch_false",
    week_day="Monday",
)

# Run dummy_task_1 if branch executes on Monday
branch >> [dummy_task_1, dummy_task_2]
```

### Custom Branch Operator
`airflow.operators.branch_operator.BaseBranchOperator`를 상속받아서 위처럼 branch 기능을 가진 custom operator를 직접 만들 수 있다.
[문서](https://airflow.apache.org/docs/apache-airflow/stable/concepts/dags.html#branching)에 아래와 같은 예제가 소개되었다.

```python
# source: https://airflow.apache.org/docs/apache-airflow/stable/concepts/dags.html#branching
class MyBranchOperator(BaseBranchOperator):
    def choose_branch(self, context):
        """
        Run an extra branch on the first day of the month
        """
        if context['data_interval_start'].day == 1:
            return ['daily_task_id', 'monthly_task_id']
        else:
            return 'daily_task_id'
```

 -  BaseBranchOperator를 상속받는다.
 -  choose_branch 메소드를 구현한다.
    -  context (`airflow.utils.context.Context` - dict-like mapping)를 input으로 받고, task id 혹은 그 리스트를 리턴한다.

위에는 간단한 예시라 하드코딩된 task id를 리턴했는데, 앞선 다른 예제들 처럼 \_\_init_\_의 argument로 task id를 받아준다면
사용성이 좀 더 높아질지도 모르겠다.

```python
# 주의: 실행해보지 않음.. 에러 가능성 농후.

class BranchScheduleIntervalOperator(BaseBranchOperator):
    def __init__(self, daily_task_ids: List[str], monthly_task_ids: List[str], **kwargs):
        super().__init__(**kwargs)
        self.daily_task_ids = daily_task_ids
        self.monthly_task_ids = monthly_task_ids

    def choose_branch(self, context):
        """
        Run an extra branch on the first day of the month
        """
        if context['data_interval_start'].day == 1:
            return self.daily_task_ids + self.monthly_task_ids
        else:
            return self.daily_task_ids
```

