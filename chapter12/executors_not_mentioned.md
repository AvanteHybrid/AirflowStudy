# 책에 언급되지 않은 executor들
[executor doc](https://airflow.apache.org/docs/apache-airflow/stable/executor/index.html)

## Debug Executor(가장 유용해 보이는 녀석입니다!)
 - Debug executor는 IDE에서도 DAG를 쉽게 테스트/디버그해볼 수 있도록 해주는 executor이다.
 - single process executor로 parellism을 지원하지 않는다.
 - sensor를 사용하는 task가 dag에 있을 경우, sensor가 이벤트를 기다리지 않고, 조건에 부합하지 않으면 바로 reschedule시킨다. (DAG 실행을 blocking 시키지 않기 위해서!)
 - fail-fast 모드로 작동 가능하다.
    - task중에 하나라도 실패하면, 나머지 task를 모두 fail 시켜서 빠른 디버깅을 가능하게 한다.
    - DAG가 커졌을 때 매우 유용하다!
 - **metastore**를 사용하기 때문에, 여전히 DB가 init/up되어 있어야 함!

### 설정법
- environmental variable 이용:
    ```bash
        export AIRFLOW__DEBUG_FAIL_FAST=True
    ```
- airflow.cfg 이용
    ```bash
        [debug]
        # Used only with ``DebugExecutor``. If set to ``True`` DAG will fail with first
        # failed task. Helpful for debugging purposes.
        fail_fast = True
    ```
### IDE에서의 세팅
1. main block setting
```python
dag = DAG(
    dag_id="listing_6_08",
    start_date=airflow.utils.dates.days_ago(3),
    schedule_interval=None,
)
...
#task....
...
if __name__ == "__main__":
    from airflow.utils.state import State

    dag.clear()
    dag.run()
```

2. IDE에서 debugger를 이용해 `AIRFLOW__CORE__EXECUTOR=DebugExecutor`를 설정
3. DAG 파일 실행!

### airflow test vs Debug Executor
 - airflow test는 원래 dag 전체가 아니라, task하나만 테스트 했었다.
 - 그러나 Airflow 2.0부터, `airflow dags test`는 DebugExecutor를 내부적으로 이용해 DAG Run을 돌릴 수 있다.
 - airflow test는 CLI 커맨드 이지만, Debug Executor는 IDE의 interactive window, debug UI를 활용할 수 있다!


## Local Executor
이미 책에 설명되어 있지만, 추가 설명을 공식 문서에서 찾았다. 우리는 LocalExecutor의 parellelism 활용 시, process의 갯수를 제한할 수 있다.
 - env var 이용:
 ```bash
    export AIRFLOW__CORE__PARALLELISM=0
 ```
 - 0으로 설정되면, 무한정 프로세스를 생성한다.
 - 0 이상의 integer가 세팅되면, 설정된 숫자만큼의 프로세스만 한번에 생성한다.


## DASK executor
스파크의 대항마인 DASK를 이용할 수 있다.

## CeleryKubernetes
셀러리와 쿠버네티스를 한꺼번에 사용할 필요가 있을 경우

## LocalKubernetes Executor
Local Executor와 Kubernetes executor를 동시에 사용해야 할 때 사용 할 수 있는 executor이다
