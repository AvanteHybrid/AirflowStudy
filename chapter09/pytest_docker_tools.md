# Using pytest-docker-tools for integration test
책에서 언급 된 `pytest-docker-tools`를 이용하면 컨테이너를 픽스쳐처럼 사용해서 테스트하려는 소스코드와 integration 테스트를 진행할 수 있다.
테스트 때만 컨테이너를 띄워놓을 수 있고, 여러개의 테스트를 동시에 돌리더라도 예기치 못한 에러들을 피할 수 있다는 점에서 강점이 있는 것 같다.

## Notes:
* 기본적으로 컨테이너는 매 session마다 clean up되고 재시작 된다.
   * 테스트들이 stateful하게 진행되는 걸 막기 위해서
* 하지만 테스트들 간에 컨테이너를 공유하는 방법도 있다.
   * pytest 실행 시 `--reuse-containers` 옵션을 사용하면 된다.
   * 단, docker container를 만들 때 꼭 `name` 속성을 설정해줘야 한다.

FYI: [pytest-docker-compose](https://github.com/pytest-docker-compose/pytest-docker-compose) 라는 패키지도 있다.
