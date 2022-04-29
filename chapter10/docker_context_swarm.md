# Docker context and docker swarm

책에서 간결한 설명을 위해 도커가 호스트 머신에서만 작동 가능한 것으로 이야기하는데 꼭 그렇지만은 않다.
[문서](https://docs.docker.com/get-started/overview/#docker-architecture)에 따르면 도커는 client-server 아키텍처로 구성이 되어있다.

![docker architecture](https://docs.docker.com/engine/images/architecture.svg)

- `dockerd`라는 도커 데몬 프로세스가 서버 역할을 하며, 도커 이미지 및 컨테이너 관련 작업을 수행한다.
- 우리가 흔히 사용하는 `docker` 라는 프로그램은 클라이언트로, REST API를 통해 `dockerd`에 작업을 요청한다.
  - 이 때 UNIX socket 혹은 network interface를 이용한다.
  - 즉, 별도의 설정이 없을 때는 UNIX socket (unix:///var/run/docker.sock)을 이용해
   로컬 호스트의 `dockerd`에게 작업을 요청하지만 설정에 따라서는 ssh 등의 네트워크 인터페이스를 이용해
   remote host의 `dockerd`에게 작업을 요청할 수 있다.

실제로 docker client는 `DOCKER_HOST`라는 환경변수를 사용한다. ssh를 통해 $USER@$REMOTE_HOST에 접근 가능한 경우, 그리고
$REMTOE_HOST에 도커가 설치된 경우 아래와 같은 명령어를 통해서 $REMOTE_HOST의 도커 이미지 리스트를 출력할 수 있다.

```bash
DOCKER_HOST=ssh://$USER@$REMOTE_HOST bash -c "docker image ls"
```

docker-py에서는 `docker_url`이라는 인자를 통해 관련된 설정을 할 수 있는 것 같다. airflow의 DockerOperator도 마찬가지로 [생성자](https://airflow.apache.org/docs/apache-airflow-providers-docker/stable/_api/airflow/providers/docker/operators/docker/index.html#airflow.providers.docker.operators.docker.DockerOperator)에서 `docker_url`이라는 인자를 받아주고 있다. 이 부분을 `ssh://$USER@$HOST` 형식으로 설정하여 리모트의 도커 환경을 사용할 수 있을 것 같다.

## [Docker context](https://docs.docker.com/engine/context/working-with-contexts/)

아무튼 도커 클라이언트는 호스트 뿐만이 아니라 여러 서버에 작업을 요청할 수 있다.
`docker context`를 통해서 어떤 서버와 통신할 지 효과적으로 관리할 수 있다.
기본적으로 Docker context는 아래와 같은 요소로 구성이 된다.

- NAME: 컨텍스트에 할당된 이름
- Endpoint configuration: 도커 서버의 endpoint 정보
- TLS info: 서버와 통신할 때의 TLS 정보
- Orchestrator: 해당 context에서 실행되는 orchestrator

docker context는 ls, create, rm, use 등 기본 도커 명령어와 흡사한 여러가지 명령어를 지원한다.
docker context ls 명령어를 통해서 위에 적혀있는 도커 컨텍스트 요소들을 확인할 수 있다.

```bash
$ docker context ls
NAME        DESCRIPTION                               DOCKER ENDPOINT               KUBERNETES ENDPOINT   ORCHESTRATOR
default *   Current DOCKER_HOST based configuration   unix:///var/run/docker.sock                         swarm
```

docker context create 명령어를 통해서 새로운 컨텍스트를 생성할 수 있다.

```bash
$docker context create $CONTEXT_NAME --docker host=ssh://$USER@$REMOTE_HOST
```

docker context use 명령어를 통해서 해당 컨텍스트를 사용하도록 세팅할 수 있다.

```bash
$docker context use $CONTEXT_NAME
```

- 이후 실행되는 도커 기본 명령어 (docker image, docker ps, docker pull, ...)는 해당 컨텍스트에서 실행이 된다.
- docker-compose 등 도커를 사용하는 프로그램에도 적용이 된다.
  - docker-compose의 경우, 명시적으로 실행할 context를 별도로 지정할 수도 있다.

    ```bash
    docker-compose --context $CONTEXT_NAME up --build -d
    ```

## [Docker swarm](https://docs.docker.com/engine/swarm/)

위에서 잠깐 언급되었지만, docker context에는 orchestrator라는 항목이 있는데 여기에 default값으로 SWARM이 들어간다.
도커에서는 자체적으로 multi-node cluster를 구축 및 관리할 수 있도록 docker swarm이라는 서비스를 제공한다.
[여기](https://dockerswarm.rocks/)를 보면 FastAPI 저자가 작성한 docker swarm 예찬(..)과 간단한 튜토리얼들을 확인할 수 있다.
별도 설치가 필요 없고, 간단한 명령어 몇 줄로 클러스터를 세팅할수 있다는 것, 그리고 도커 명령어와 유사한 명령어들을 제공해
추가적인 학습이 덜 필요하다는 것이 가장 큰 장점인 듯하다.
잠깐 살펴보았는데 마이크로서비스들의 조직과 운영에 특장점이 있는 것 처럼 보인다.
Distributed job의 실행 및 스케쥴링에 효과적인지는 좀 더 살펴보아야 할 것 같다.