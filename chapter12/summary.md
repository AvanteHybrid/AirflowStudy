# Operating Airflow in production

## Airflow architectures
기본적으로 airflow는 아래와 같이 구성이 된다.

![fig_12.1](./images/fig_12.1.png)

- Webserver
    - airflow 프로세스로 웹 서비스 구성
    - 실행 내역 등을 visualize
- Scheduler:
    - airflow 프로세스
    - DAG 파일을 파싱해서 metastore에 정보를 저장
    - Task 실행을 결정해서 task queue에 작업 전달.
    - SchedulerJob은 아래와 같은 세부 구성 요소로 나눌 수 있다.
        ![figure 12.4](./images/fig_12.4.png)
        - DAG Processor
            - while True 루프로 돌며, 주기적으로 DAG 파일을 파싱해서 metastore에 저장한다.
            - dynamic DAG 등에 대응하기 위해서 파일 변경이 없어도 검사를 한다.
        - Task Scheduler
            - 마찬가지로 while True 루프로 돌며, 각 taskinstance가 실행할 조건이 되었는지 확인한다.
            - task를 queued state로 셋업하면, 해당 task의 실행은 executor가 관장한다.
        - Task Executor
            - queued task를 실행하며, 실행 상태를 metastore에 업데이트한다.
            - heartbeat 메소드를 통해 해당 task의 상태를 주기적으로 점검한다.

- Database:
    - airflow 외부의 프로세스로, metastore 데이터베이스를 구성.
    - 여러 DB 백엔드로 세팅할 수 있지만, MySQL과 PostgreSQL이 권장된다.
        - concurrent write 기능이 제공되지 않는 SQLite는 SequentialExecutor와 함께 데모용으로만 사용해야한다.
    - airflow는 내부적으로 Python ORM (SQLAlchemy)를 사용한다.
        - migration 관리를 위해서는 alembic이 사용되고 있으며, airflow 버전 업에 따른 metastore 스키마 변동이 생기는 경우 `airflow db upgrade` 등의 명령어를 통해 이를 반영해야한다.
- Executor:
    - SequentialExecutor (default)
        - 가장 간단하지만, 데모용으로만 사용해야한다. 한 번에 한 task만 실행 가능하다.
    - LocalExecutor
        - concurrent한 task 실행이 가능하다. (default 32)
        - 하지만 한 노드에서만 실행 된다.
    - CeleryExecutor
        - 여러 노드에서 실행이 가능하다.
        - RabbitMQ, Redis, AWS SQS 등의 queue를 제공한다.
        - Flower라는 모니터링 툴이 제공된다.
    - KubernetesExecutor
        - kubernetes API를 이용해 airflow task를 분배한다.

## Installing each executor
- SequentialExecutor: 디폴트 세팅
- LocalExecutor
    - 상술한 방법으로 MySQL 혹은 PostgreSQL을 세팅해야한다. pip install 시 extra 디펜던시를 지정할 수 있다.
        ```bash
        pip install apache-airflow[postgres]
        ```
- CeleryExecutor
    - DAG 폴더를 모든 Celery worker가 접근 가능한 곳에 세팅해두어야 한다.
    - 상술한것 처럼 extra depencecy를 지정해서 설치하고, 환경변수로 executor를 설정해야한다.
    - queueing system (broker)과 airflow metastore 인식을 위한 추가 설정이 필요하다. 설정관련 내용은 아래 모아두었다.
    - `airflow celery flower` 명령어를 통해 flower를 실행할 수 있다. 대시보드를 통해 태스크 실행, 리소스 등을 모니터링 할 수 있다.
- KubernetesExecutor
    - Helm을 사용해 셋업한다. 저술 시점에는 공식 Helm Chart가 깃에는 올라오고 Helm repositorires에는 릴리즈가 되지 않았었다. 현재는 릴리즈가 되어있으니 [이전 자료](../chapter10/summary.md)에 소개된 방법으로 설치가 가능하다.
    - DAG 폴더를 모든 pod에서 접근 가능하도록 설정해두어야 한다.
        - PersistentVolume을 생성한다.
            - 모든 worker에서 접근이 가능하도록 NFS에 DAG파일들을 저장/sync 한다.
            - 해당 경로를 PersistentVolume으로 생성하여 Task 실행시 PVC를 통해 해당 경로를 mount하도록 설정한다.
            - NFS는 자체적으로 인터넷 통신 인터페이스가 제공이 되지 않는데, 아래 두 가지 방법으로 DAG 파일들을 sync한다.
                - (push method): FTP 서버를 구성하여 NFS를 마운트한다. CI/CD를 통해서 DAG 깃 레포지토리가 업데이트 될 때마다 변경사항을 FTP 서버로 전송한다.
                - (pull method): Git-sync용 DAG를 작성해서 주기적으로 master 브랜치를 pull 받는다.
        - Git-sync init 설정
            - airflow에서는 쿠버네티스에서 task 실행 시 side-car 컨테이너에서 git-sync할 수 있는 옵션을 제공한다. 아래에 관련 설정을 정리해두었다.
        - DAG 파일들 자체를 airflow 이미지에 포함해서 빌드를 하기도 한다.
            - 내용이 제일 자세한 거 보니 이게 best practice인 것 같다.
            - 이미지 빌드 단계에서 dependency conflict 등을 잡아낼 수 있는 등의 장점이 있다.
            - dag 수정으로 인해 매번 airflow 패키지 설치를 다시 하지 않도록 dag COPY 명령어를 최대한 나중에 작성

## Capturing logs of all Ariflow processes

- web server log
  - 모든 request와 관련된 정보 등이 기록 된다.
  - airflow webserver 실행 시 access log와 error log를 특정 파일로 저장하도록 세팅할 수 있다.
    ```bash
    airflow webserver -access_logfile $FILENAME -error_logfile $FILENAME
    ```
      - $AIRFLOW_HOME에서의 상대 경로로 저장된다.

- 나머지 scheduler, task 등의 log는 $AIRFLOW_HOME/logs 밑에 저장된다.
- 외부 storage 로그를 저장할 수도 있다. (remote logging)

## Visualizing and monitoring Airflow metrics
Airflow 운영을 위해 시스템에 대한 모니터링이 필요한 순간이 올 것이다. 주로 아래와 같은 측면에서 모니터링이 필요하다.
- latency
  - webserver request 평균 response 속도, queued task 평균 대기 시간 등
- traffic
  - 분당 실행되는 평균 task 수 등
- errors
  - zombie task 갯수
- saturation
  - cpu 로드 등의 하드웨어 부하
  - db, kubernetes 등 외부 서비스의 부하 등

위와 같은 정보를 airflow 시스템으로부터 받아와 web ui로 구성하기까지 세팅할 수 있는 여러 방법이 있을텐데,
책에서는 아래와 같은 구조를 설명한다.
![fig_12.16](./images/fig_12.16.png)

- StatsD
   - metrics collection system으로, push model이다.
   - hierarchical한 데이터 모델 구조를 갖는다.
   - Airflow에서는 StatsD integration을 extra dependency로 제공한다.
   - 즉, Airflow에서 이벤트 발생 등에 대한 statistics를 StatsD로 push한다.

- Prometheus
   - 마찬가지로 metric collection system으로, pull 모델이다.
   - 즉, source에 주기적으로 요청을 날려 statistics를 받아온다.
   - key-value label 형태의 데이터 모델 구조로 인해 위에 비해 쿼리가 자유롭다.
   - 하지만 Airflow에서는 Prometheus 데이터 모델 형식의 메시지를 지원하지 않아서
     위 그림과 같이 StatsD를 중간에 끼고 statsd_expoerter를 통해 데이터를 변환해야한다.

- Grafana
   - metrics visualization 서비스다.
   - backend db로 주기적으로 쿼리를 날려 결과를 visualize 하는데, 여기에 ms 단위의 딜레이가 생길 수 있다.


## How to get notified of a failing task

- DAG 혹은 Operator 레벨에서 `on_failure_callback`을 넘겨줄 수 있다. 이를 통해 custom error notification을 받을 수 있다.
- `email_on_failure`를 통해서 airflow에서 자체적으로 보내는 이메일 알림을 받을 수 있다. 물론 SMTP 관련 설정이 필요하다.
    - DAG의 default_args에 `{'email': 'user@domain.co'}` 등으로 넘겨주면 된다.
- SLA 설정도 가능한데, [지난 챕터](../chapter11/summary.md)에서 살펴보았으니 넘어가자.


## Scalability and performance
이 절에서는 scalablity와 performance 관점에서 airflow를 어떻게 튜닝할 수 있는 지 살펴본다.

- 아래 세팅을 통해 concurrency와 parallelism을 제어할 수 있다.
 ![table.12.3](./images/table_12.3.png)
- airflow scheduler가 database에 크게 의존하는데, 아래 설정값의 조정을 통해 db query 주기를 제어할 수 있다.
    ```text
    AIRFLOW__SCHEDULER__SCHEDULER_HEARTBEAT_SEC
    AIRFLOW__SCHEDULER__SCHEDULER_HEALTH_CHECK_THRESHOLD
    AIRFLOW__SCHEDULER__PARSING_PROCESSES
    AIRFLOW__SCHEDULER__DAG_DIR_LIST_INTERVAL
    ```
- Airflow >= 2.0 에서는 multiple scheduler를 사용할 수 있다.
    - row-level locking을 사용해 DB 백엔드 버전에 제약이 있다. (PostgreSQL>=9.6, MySQL>=8)
    - 별도의 세팅 필요 없이 scheduler processs를 더 실행하면 된다. (`airflow scheduler` 명령어)


## Setup configurations

```bash
# Airflow 1 (>= 1.10.10)에서 DAG serialization 활성화하기
AIRFLOW__CORE__STORE_DAG_CODE=True
AIRFLOW__CORE__STORE_SERIALIZED_DAGS=True

# SQLite 아닌 다른 DB 백엔드 설정하기
AIRFLOW__CORE__SQL_ALCHEMY_CONN=${protocol}://$username:$password@localhost:$db_port/airflow

# 기본 example DAG 로딩하지 않게 설정하기
AIRFLOW__CORE__LOAD_EXAMPLES=False
# 기본 example connection 로딩하지 않게 설정하기
AIRFLOW__CORE__LOAD_DEFAULT_CONNECTIONS=False

# 스케쥴러 관련 셋업
AIRFLOW__SCHEDULER__PROCESSOR_POLL_INTERVAL=30 # scheduler loop time sleep value
AIRFLOW__SCHEDULER__MIN_FILE_PROCESS_INTERVAL=0 # minimum interval for file processing
AIRFLOW__SCHEDULER__DAG_DIR_LIST_INTERVAL=300 # interval to refresh list of files in dag dir
AIRFLOW__SCHEDULER__PARSING_PROCESSES=1 # parsing에 사용할 최대 process 개수

# DAG FOLDER 지정
AIRFLOW__CORE__DAGS_FOLDER=$DAG_DIR

# task concurrency
AIRFLOW__CORE__DAG_CONCURRENCY=32
AIRLOFW__CORE__MAX_ACTIVE_RUNS_PER_DAG=4

# Celery Executor setup
AIRFLOW__CORE__EXECUTOR=CeleryExecutor
AIRFLOW__CELERY__BROKER_URL=redis://localhost:6379/0
AIRFLOW__CELERY__RESULT_BACKEND=db+postgresql://user:pass@localhost/airflow

# Kubernetes setup - dag volume
AIRFLOW__KUBERNETES__DAGS_VOLUME_CLAIM=$PV_NAME
# Kubernetes setup - git sync
AIRFLOW__KUBERNETES__GIT_REPO = https://mycompany.com/repository/airflow
AIRFLOW__KUBERNETES__GIT_BRANCH = master
AIRFLOW__KUBERNETES__GIT_SUBPATH = dags
AIRFLOW__KUBERNETES__GIT_USER = username
AIRFLOW__KUBERNETES__GIT_PASSWORD = password
AIRFLOW__KUBERNETES__GIT_SSH_KEY_SECRET_NAME = airflow-secrets
AIRFLOW__KUBERNETES__GIT_DAGS_FOLDER_MOUNT_POINT = /opt/airflow/dags
AIRFLOW__KUBERNETES__GIT_SYNC_CONTAINER_REPOSITORY = k8s.gcr.io/git-sync
AIRFLOW__KUBERNETES__GIT_SYNC_CONTAINER_TAG = v3.1.2
AIRFLOW__KUBERNETES__GIT_SYNC_INIT_CONTAINER_NAME = git-sync-clone
# Kubernetes setup - dag in imave
AIRFLOW__KUBERNETES__DAGS_IN_IMAGE=True

# Remote logging
AIRFLOW__CORE__REMOTE_LOGGING=True
AIRFLOW__CORE__REMOTE_LOG_CONN_ID=$CONN_ID

# SMTP setup
AIRFLOW__SMTP__SMTP_HOST=smtp.gmail.com
AIRFLOW__SMTP__SMTP_MAIL_FROM=myname@gmail.com
AIRFLOW__SMTP__SMTP_PASSWORD=abcdefghijklmnop
AIRFLOW__SMTP__SMTP_PORT=587
AIRFLOW__SMTP__SMTP_SSL=False
AIRFLOW__SMTP__SMTP_STARTTLS=True
AIRFLOW__SMTP__SMTP_USER=myname@gmail.com
```