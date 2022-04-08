# Connection in Airflow

앞서 챕터4에서 PostgresOperator 사용 시 connection에 대한 내용이 나왔었는데, Connection을 추가 및 관리하는 방법만 간단히 다루고 컨셉에 대한 자세한 설명은 없었던 거 같아서 정리해보고자 한다.

## Connection에 대해
Airflow는 이번 챕터에서 보았듯이, 외부 시스템이나 서비스와 interaction 하는 일이 많다.
그렇기 때문에, Airflow에서는 Connection이라는 concept을 제공하여 외부 서비스에 사용되는 credential과 같은 정보들을 쉽게 관리하고 사용할 수 있도록 한다.

Connection은 사실 상 외부 시스템에 접근하기 위해 사용되는 정보들의 집합이다.
Username, password, hostname, external system type (conn_type), port 등 여러가지가 있을 것이다.
각각의 Connection은 `conn_id`라는 unique한 이름을 가지고, 이 이름으로 connection을 가져올 수 있다.

## Connection을 사용하는 방법
### Template을 사용하는 방법
DAG 코드에서 template 기능을 사용해 바로 아래와 같이 사용할 수 있다.
```bash
echo {{ conn.<conn_id>.host }}
```
`conn.<conn_id>`를 이용해서 Connection 정보를 dictionary로 가져오고 template 방식으로 접근하게 된다.

### Hook을 사용하는 방법
Hook은 외부 시스템에 접근할 때 사용하는 authentication 과 connection등을 담당한다.
이를 이용해 쉽게 외부 시스템의 API를 사용할 수 있고, 대부분 Operator 내부에 built-in으로 들어있다고 하고 저번에 넘어갔던걸로 기억한다.
하지만 이번 챕터에서처럼, custom operator를 작성 할 때 Operator 내부에 Hook을 관리하고 사용해야 할 일이 있을 것이다.

본론으로 넘어가면, Hook과 Connection은 서로 한 몸이라고 볼 수 있다.
각각의 Hook은 대체로 default `conn_id`를 갖고 있어서, 자동으로 Hook이 사용할 Connection을 찾고 이를 사용해서 authentication 등을 진행한다.
예를 들면, `PostgresHook` 같은 경우에 `postgres_default`라는 `conn_id`를 갖고 있어서 자동으로 이 아이디를 찾게 된다.
Hook마다 connection id를 넘겨줄 수도 있는데 이건 Hook 클래스마다 달라서 doc을 참고해야한다.


참고:
* [List of Connections provided by Airflow](https://airflow.apache.org/docs/apache-airflow-providers/core-extensions/connections.html)
* [List of Hooks provided by Airflow](https://airflow.apache.org/docs/apache-airflow/stable/_api/airflow/hooks/index.html)

References
* [Connections & Hooks](https://airflow.apache.org/docs/apache-airflow/stable/concepts/connections.html)