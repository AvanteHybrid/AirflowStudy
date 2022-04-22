# Testing

코드가 올바르게 동작한다는 것을 보장하기 위해서 올바른 테스트 코드가 작성되어야 한다.
Unit test를 통해서 개별 함수 및 work unit이 잘 작동하는 지 확인하고, Integration test를 통해서 여러 컴포넌트를 붙였을 때 잘 작동하는 지 살펴야 한다.
Airflow DAG 및 Operator들도 마찬가지인데, 여러 외부 시스템을 활용하고, 많은 작업을 orchestration하는 Airflow의 특성상 테스트 작성에 애로 사항이 많다.
이 챕터는 Airflow DAG 개발 시 pytest를 이용하여 테스트 코드를 작성하는 유용한 방법들을 제안하며, 보다 자세하게는 아래와 같은 내용을 다룬다.

- DAG integrity test
- Context를 활용하지 않는 단순한 Operator 테스트
- Context를 활용하는 Operator들의 테스트
- DAG 단위의 테스트

## DAG Integrity test

DAG이 acyclic한지, task id에 중복이 없는 지 DAG의 구조적 무결성을 검증하기 위한 테스트를 일컫는다.
물론 DAG을 업로드하면 Airflow system이 해당 DAG을 파싱하고 직렬화하는 과정에서 이러한 문제들을 리포트해준다.
하지만 업로드 및 배포 전에 이러한 무결성을 검증하는 것이 중요하다.
아래와 같은 예제를 통해 dags 폴더 안에 있는 모든 DAG의 구조적 무결성을 검증할 수 있다.
DAG 파이썬 스크립트에서 Dag object를 찾아서 `airflow.utils.dag_cycle_tester.check_cycle` 함수를 실행하면 된다.
Cycle 판별 뿐만 아니라 Operator선언 시 missing positional arg를 찾아주는 등의 검사들도 한다.

```python
# slightly modified from the following source
# https://github.com/BasPH/data-pipelines-with-apache-airflow/blob/master/chapter09/tests/dags/test_dag_integrity.py

import glob
import importlib.util
import os

import pytest
from airflow.models import DAG
# Dag's test_cycle method has been removed
from airflow.utils.dag_cycle_tester import check_cycle

# Glob pattern to resursively find all the dag files under dags folder
DAG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "dags/**/*.py")
# Recursively find all the dags
DAG_FILES = glob.glob(DAG_PATH, recursive=True)

# Parameterize to run test against every dag files
@pytest.mark.parametrize("dag_file", DAG_FILES)
def test_dag_integrity(dag_file):
    """Import DAG files and check for DAG."""
    module_name, _ = os.path.splitext(dag_file)
    module_path = os.path.join(DAG_PATH, dag_file)

    # import module using path to python file
    # equivalent to from some.directories import file_name as module
    mod_spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(mod_spec)
    mod_spec.loader.exec_module(module)

    dag_objects = [var for var in vars(module).values() if isinstance(var, DAG)]
    assert dag_objects

    for dag in dag_objects:
        # Test cycles
        check_cycle(dag)
```

## Context를 활용하지 않는 단순한 Operator 테스트 작성법

Custom operator를 작성했다면, 해당 operator가 잘 작동하는지 테스트하는 코드도 함께 작성해야한다.
Operator의 복잡도에 따라서 단순한 Unittest로 커버가 가능할 때가 있고, 그렇지 않을 때가 있다.
좀 더 엄밀히 말하면, 특정 Opeartor가 task instance의 context 정보를 활용하는 경우,
단순한 Operator unittest로는 커버할 수 없어 Task 및 DAG 단위에서 실행하는 test가 필요하다.
후자에 대해서는 조금 뒤에 다시 다루고, 여기서는 단순한 형태의 Operator Unittest 작성법에 대해 살펴본다.
사실 별 다를건 없고, operator의 execute 메소드를 활용해서 result가 제대로 출력되는지 검증하면 된다.
예제에서도 주로 airflow 관련 내용이라기보단 pytest 및 pytest-mock과 관련된 내용을 설명한다.

### Mock 사용하기

```python
from airflow.models import Connection
from airflow.operators.bash import BashOperator

from airflowbook.operators.movielens_operator import (
    MovielensPopularityOperator,
    MovielensHook,
)

# arg name을 mocker로 두면 fixture를 통해서 pytest_mock.MockFixture object를 전달받을 수 있다.
def test_movielenspopularityoperator(mocker):
    # MovielensHook.get_connection을 unittest.mock.MagicMock으로 대체한다.
    # 해당 메소드가 콜 되면 그냥 전달받은 return_value를 반환한다
    mock_get = mocker.patch.object(
        MovielensHook,
        "get_connection",
        return_value=Connection(conn_id="test", login="airflow", password="airflow"),
    )
    task = MovielensPopularityOperator(
        task_id="test_id",
        conn_id="testconn",
        start_date="2015-01-01",
        end_date="2015-01-03",
        top_n=5,
    )
    result = task.execute(context=None)
    # 반환하는 result의 length 검증
    assert len(result) == 5
    # MagicMock에 테스트 컨텍스트가 저장되어 이를 검사할 수 있다.
    assert mock_get.call_count == 1
    mock_get.assert_called_with("testconn")
```

책에서 pytest 및 pytest-mock과 관련해서 언급한 내용을 아래와 같이 정리한다.

- pytest로 실행되기 위한 조건
    - 테스트 스크립트의 filename이 `test_`로 시작해야한다.
    - 테스트 스크립트 내의 테스트 함수가 `test`로 시작해야한다.

- 유닛테스트에서 mocking code를 작성할 때, 함수가 정의된 클래스가 아닌, 테스트하고자 하는 클래스의 메소드 혹은 attribute를 대체해야한다.
    - 테스트하고자 하는 클래스의 특정 메소드가 superclass에 정의되어있더라도, mocker.patch.object()의 첫 인자로 superclass를 넣지 말고 직접 테스트하고자 하는 클래스를 넣어줘야한다.

### Temp path 사용하기

```python
def test_json_to_csv_operator(tmp_path):
    print(tmp_path.as_posix())

    input_path = tmp_path / "input.json"
    output_path = tmp_path / "output.csv"
    ...
```

파일 입출력이 필요한 operator의 경우, 테스트에서 temp path를 활용해서 테스트 종료 후 해당 경로가 삭제되는 것을 보장할 수 있다.
테스트 함수 내에서 `tempfile` 패키지를 호출할 필요 없이, pytest의 fixture를 활용해서 temp path를 전달 받을 수 있다.
테스트 함수에서 tmp_path라는 이름의 argument를 받아주면 되는데, 더 자세한 내용은 [해당 문서](https://docs.pytest.org/en/6.2.x/tmpdir.html)를 참고해보자.
시스템에 따라, 설정에 따라 temp path로 잡는 경로가 다를 것 같은데 실행해보니 위 함수를 실행해보니 아래와 같은 경로가 출력되었다.

- /tmp/pytest-of-jijokim/pytest-2/test_json_to_csv_operator0

## Context를 활용하는 복잡한 Operator들의 테스트 작성

template_fields를 활용해서 렌더링 하는 등 task instance의 context 정보를 활용하는 복잡한 Operator의 경우에는
위와 같이 단순하게  execute() 메서드를 호출하는 것으로 테스트할 수가 없다.

- 먼저 DAG object를 생성해야한다.
- 해당 DAG object를 Operator 생성자에 전달해야한다.
- Operator에서 execute가 아닌 run 메소드를 실행해야 한다.
    - 해당 메소드는 task instance를 생성하여 operator를 실행한다.

문제는 task instance 생성 및 실행에 있어서 airflow db와 통신을 시도한다는 것이다. 해결 방법은 아래와 같다.
- 모든 db 통신을 mock한다. (...)
- 그냥 테스트용 airflow db를 띄운다.
  - `airflow db init` 명령어
  - AIRFLOW_HOME이 잘 설정되었느지 확인하자.

위 문제는 그냥 테스트 airflow db를 띄우는걸로 해결했지만, 많은 Operator들이 외부의 시스템과의 통신을 필요로 한다.
`pytest_docker_tools`를 이용할 경우 도커 형태로 외부 시스템 테스팅 환경을 구축할 수 있다.

```python
# Source: https://github.com/BasPH/data-pipelines-with-apache-airflow/blob/master/chapter09/tests/airflowbook/operators/test_movielens_operator2.py
pytest_plugins = ["helpers_namespace"]

import datetime
import os

import pytest
from airflow.models import Connection
from pytest_docker_tools import fetch, container

from airflowbook.operators.movielens_operator import (
    MovielensHook,
    MovielensToPostgresOperator,
    PostgresHook,
)

# docker pull postgres:11.1-alpine
postgres_image = fetch(repository="postgres:11.1-alpine")

# create pytest fixture for postgres container
postgres_container = container(
    image="{postgres_image.id}",
    environment={"POSTGRES_USER": "testuser", "POSTGRES_PASSWORD": "testpass"},
    ports={"5432/tcp": None}, # if value is None, ports will be mapped to a random avaialble port in host
    volumes={
        os.path.join(os.path.dirname(__file__), "postgres-init.sql"): {
            "bind": "/docker-entrypoint-initdb.d/postgres-init.sql"
        }  # bind init sql script to docker path
    },
)


def test_movielens_to_postgres_operator(mocker, test_dag, postgres_container):
    # patch connection to movelens
    mocker.patch.object(
        MovielensHook,
        "get_connection",
        return_value=Connection(conn_id="test", login="airflow", password="airflow"),
    )
    # patch connection to postgres
    mocker.patch.object(
        PostgresHook,
        "get_connection",
        return_value=Connection(
            conn_id="postgres",
            conn_type="postgres",
            host="localhost",
            login="testuser",
            password="testpass",
            port=postgres.ports["5432/tcp"][0],
        ),
    )

    # create task for the operator
    task = MovielensToPostgresOperator(
        task_id="test",
        movielens_conn_id="movielens_id",
        start_date="{{ prev_ds }}",
        end_date="{{ ds }}",
        postgres_conn_id="postgres_id",
        insert_query=(
            "INSERT INTO movielens (movieId,rating,ratingTimestamp,userId,scrapeTime) "
            "VALUES ({0}, '{{ macros.datetime.now() }}')"
        ),
        dag=test_dag,
    )

    # test if intialized DB stores nothing
    pg_hook = PostgresHook()
    row_count = pg_hook.get_first("SELECT COUNT(*) FROM movielens")[0]
    assert row_count == 0

    # run task
    pytest.helpers.run_airflow_task(task, test_dag)


    # test if DB stores proper information after task run
    row_count = pg_hook.get_first("SELECT COUNT(*) FROM movielens")[0]
    assert row_count > 0
```

github에 올라온 예제에서는 책의 예제와 다르게 pytest-helpers-namespace를 사용하고 있다.
사용법은 이 [문서](https://pypi.org/project/pytest-helpers-namespace/#:~:text=This%20plugin%20does%20not%20provide,without%20having%20to%20import%20them.)에 간략히 소개되어있다.
이 예제의 `conftest.py`의 경우 아래와 같이 작성되어있다.

```bash
import datetime

import pytest
from airflow.models import DAG, BaseOperator

pytest_plugins = ["helpers_namespace"]


@pytest.fixture
def test_dag():
    return DAG(
        "test_dag",
        default_args={"owner": "airflow", "start_date": datetime.datetime(2015, 1, 1)},
        schedule_interval="@daily",
    )


@pytest.helpers.register
def run_airflow_task(task: BaseOperator, dag: DAG):
    dag.clear()
    task.run(
        start_date=dag.default_args["start_date"],
        end_date=dag.default_args["start_date"],
        ignore_ti_state=True,
    )
```

## DAG 단위의 테스트

작성한 Custom Operator가 잘 작동하는 지 테스트하는 것 만큼이나 실제 작성한 DAG이 잘 작동하는 지
확인하는 것도 중요하다.
암울하게도 여기에 대해서는 뾰족한 수가 없어서, 테스트 환경을 구성해서 테스트 환경에서 잘 작동이 되는 것을
시간을 두고 검증한 이후, 이를 실제 프로덕션으로 릴리즈 하는 방식을 택하는 수 밖에 없다.
단순하게는 test / production 환경으로 나뉘겠지만, 세분화하면 DTAP(deploymetn, test, acceptance, production)로 환경을 나눌 수 있다. 각각을 git에서 별도의 브랜치로 관리하며, 별도 브랜치마다 환경을 분리해서 운영하는 것을 권장한다.
물론 각 환경을 얼마나 실제 production에 가깝게 구성할 지에 대해서는 고민이 필요한 부분이며, Whirl 등의 서비스를 production 환경 시뮬레이션에 이용할 수 있다고 한다.
