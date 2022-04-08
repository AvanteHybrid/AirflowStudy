# Communicating with external systems

### This chapter covers
 - 에어플로우 외부의 시스템과 상호작용 하는 오퍼레이터들로 작업하기
 - 외부 시스템에 오퍼레이터 적용하기
 - 두개의 외부 시스템 사이에서 데이터를 교환하는 오퍼레이터 적용하기
 - 외부 시스템에 접속하는 태스크들 테스트하기

### 챕터 개요
 - 7.1: 외부 시스템을 사용하는 오퍼레이터를 적용해보기
 - 7.2: 두 외부 시스템 간에서 데이터를 교환하는 오퍼레이터를 적용해 보기
이 챕터는 외부 시스템을 사용해보는 예제를 보여주는 것에 집중하고 있기 때문에, 정리할 내용이 많지 않았다... 그나마도 우리가 쓰지 않는 시스템(AWS 등)에 관한 예제들이라서, 크리티컬하지 않은 예제들의 경우 설명을 건너뛰었다.

### 외부 시스템의 정의
 - airflow가 아닌 다른 프로그램
 - and
 - airflow가 돌고 있는 머신이 아닌 것

### 7.1 클라우드 서비스에 접속하기
 - 에어플로우는 다양한 외부 시스템(서비스)에 접속하는 오퍼레이터를 제공하고 있다.
 - 에어플로우는 점점 더 다양한 외부 시스템 오퍼레이터를 제공하고 있다.
 - 외부 시스템 오퍼레이터는 외부 시스템을 이용하기 위해 제공되는 python package의 많은 기능을 커버하고, 단순화시킴으로써 에어플로우 개발자가 더 간편하게 개발을 할 수 있도록 돕는다.
 - 그러나, 단순화 시킨 만큼, 에어플로우에서 제공하지 않는 기능들이 있을 수 있고, 혹은 에어플로우의 오퍼레이터에서 포함시키기 어려운 로직이 있을 수 있다. 이러한 경우 기존대로 PythonOperator를 붙여서 사용해야 한다.

#### 7.1.1 extra dependencies 설치하기
 - 이전 챕터에서 보았듯이, airflow2로 업데이트되면서 airflow core에서 airflow의 실행에 핵심적이지 않은 많은 오퍼레이터들이 방출(?)되었고, 이러한 오퍼레이터들을 사용하기 위해서는 따로 설치를 해주어야 한다.
 - 외부 시스템에 접속하는 오퍼레이터도 airflow와 별개로 설치를 진행해야 한다.
 - 대부분의 경우 `$ pip install apache-airflow-providers-{service 명}` 으로 설치를 할 수 있다.

#### 7.1.2 머신 러닝 모델 개발하기
 - 이 섹션은 이 챕터 내에서 외부 시스템 오퍼레이터를 사용하는 방법을 설명하기 위해 특수한 예제를 설명하는 부분으로, AWS를 이용한 머신러닝 예제를 들고 있다.
 - 우리가 사용하는 Gcloud의 경우 [여기](https://airflow.apache.org/docs/apache-airflow-providers-google/stable/operators/cloud/index.html)에서 정보를 찾아볼 수 있다.
 - GCS의 경우, [여기](https://airflow.apache.org/docs/apache-airflow-providers-google/stable/_api/airflow/providers/google/cloud/operators/gcs/index.html#airflow.providers.google.cloud.operators.gcs.GCSObjectCreateAclEntryOperator)에서 찾아볼 수 있다.
 - 앞서 밝혔듯, 오퍼레이터에서 제공하는 기능이 아니거나, 로직이 복잡한 경우 PythonOperator를 이용한다. 다만, 외부 시스템과 연결할 수 있는 Hook은 에어플로우에서 제공하는 경우가 있으므로, 여전히 조금 더 간편하게 코드를 짤 수 있도록 지원한다고 할 수 있다.

##### 외부 시스템 오퍼레이터로 기능이 충분한 경우
```python
load_csv = GCSToBigQueryOperator(
    task_id='gcs_to_bigquery_example',
    bucket='cloud-samples-data',
    source_objects=['bigquery/us-states/us-states.csv'],
    destination_project_dataset_table=f"{DATASET_NAME}.{TABLE_NAME}",
    schema_fields=[
        {'name': 'name', 'type': 'STRING', 'mode': 'NULLABLE'},
        {'name': 'post_abbr', 'type': 'STRING', 'mode': 'NULLABLE'},
    ],
    write_disposition='WRITE_TRUNCATE',
)
```

##### 외부 시스템 오퍼레이터로 기능이 충분하지 않은 경우
 - 에어플로우에서 제공하는 훅을 python function안에 넣어 사용한다.
    ```python
    from airflow.providers.google.cloud.hooks.gcs import GCSHook

    ...

    def _complex_logic():
        gcs_hook = GCSHook()
        gcs_hook.download(
            bucket_name="{버켓이름}"
            ...
        )
    ```

#### 7.1.3 외부 시스템을 로컬에서 개발하기
 - 외부 시스템에 접속하기 위해서는 서비스 키가 필요한 경우가 많다(Access Control)
 - export를 이용해서 credential을 설정할 수 있지만, **airflow.cfg**를 이용해서 설정할 수도 있다.
    ```bash
    [secrets]
    backend = airflow.providers.google.cloud.secrets.secret_manager.CloudSecretManagerBackend
    backend_kwargs = {"connections_prefix": "example-connections-prefix", "variables_prefix": "example-variables-prefix", "gcp_key_path": "/somewhere/key.json"}
    ```
 - 이전에 소개되었던 `$ airflow tasks test {dag 명} {task 명} {execution date}` 기능을 이용해 credential/connection을 테스트하자.

##### Useful tips
1. Unique name이 필요한 경우 execution date를 활용할것.
예를 들어, GCS에서 `data_logs`라는 bucket을 creation 하고 log를 담는 태스크가 있다고 할 때, bucket name이 run에 상관없이 동일하다면, 첫 번째 run에서는 문제가 없겠지만, 두 번째 run에서는 bucket creation이 exception을 뱉어내며 영원히 fail될 수 있다. 따라서, 지속적으로 bucket creation이 필요한 경우, `data_logs_{execution_date}`와 같이 포매팅해주는 것이 좋다.
2. 대부분의 외부시스템에서는 wait_for_completion을 True로 세팅하고, check_interval을 reasonable하게 설정할 것
 - Airflow의 외부 시스템 오퍼레이터는 대부분 요청을 보내고, 응답을 기다리지 않는 fire and forget을 default로 하고 있다. 따라서, `wait_for_completion`이 `True`가 아니라면,요청을 보내는 것에만 성공해도 task가 pass하게 될 수 있다. 외부 시스템에 요청한 job이 끝나고 난 다음에 task가 pass하길 바란다면 `wait_for_completion`을 True로 세팅하자!

### 7.2 외부 시스템 간에 데이터를 옮기기(A-to-B operator)
다양한 이유로 한 외부 시스템에서 다른 외부 시스템으로 데이터를 옮길 상황들이 발생한다. 따라서, airflow에서는 한 외부 시스템에서 다른 외부 시스템으로 데이터를 옮겨주는 operator들을 제공하고 있다.

#### 외부 시스템 간에 데이터를 옮기는 두 가지 방법(약간의 뇌피셜)
두 외부 시스템 간에 데이터를 옮기는 경우, 두 외부 시스템이 하나의 회사에 속해있는지, 혹은 협력을 하고 있는지에 따라서 A-to-B operator는 두 가지 방식으로 작동할 것이다.
1. A와 B 서비스간에 직접 통신이 가능하여, airflow가 실행되는 machine에 데이터를 보낼 필요가 없음
    - A에서 airflow에 데이터를 전송하고, airflow가 B로 데이터를 전송하지 않으므로 속도가 빠를 수 있다.
    - airflow가 실행되는 머신은 요청을 보내기만 하면 되므로, 컴퓨팅 파워/메모리를 소모하지 않아 가볍다.
    - 뇌피셜로 보건데, GCSToBigQueryOperator 같은 경우가 이에 해당할 것이다.
2. A와 B 서비스간에 직접 통신이 되지 않고, airflow가 실행되는 machine이 medium이 되어 주어야 하는 경우
    - airflow가 실행되는 machine이 medium으로 작용하기 때문에, 1에 비해 속도가 느릴 수 있다.
    - 한번에 처리하는 데이터의 사이즈가 너무 크고 여러개인 경우 Out Of Memory가 일어날 수 있다.
    - [Google Transfer Operators](https://airflow.apache.org/docs/apache-airflow-providers-google/stable/operators/transfer/index.html)

#### 작은 데이터 vs 큰 데이터
 - 특히 두 시스템 간에 데이터를 옮기면서 고려해야 할 것은 옮겨지는 데이터의 크기이다.
 - 데이터가 크지 않은 경우 "메모리에만 데이터를 받아와서 옮기는 A to B Operator"를 사용해도 문제가 없지만,
 - 데이터가 큰 경우, "받아온 데이터를 임시 파일로 만들고, 그걸 다시 읽어서 옮기는 A to B Operator"를 사용하는 것이 바람직 할 수 있다.
 - 다만 이 경우, local machine의 저장 용량이 충분해야 할 것이다.

#### 무거운 job을 아웃소싱하기

##### 에어플로우를 바라보는 두 가지 시선
1. airflow는 task를 조율할 뿐, task의 동작이 세부적으로 기술되는 곳이 되어서는 안된다!
vs
2. **airflow는 task를 조율할 뿐 아니라, task의 동작이 세부적으로 기술되고, 실행하는 곳이 되어도 된다!** -> apache spark/docker와 같은 시스템으로 task의 동작/실행을 이양하자