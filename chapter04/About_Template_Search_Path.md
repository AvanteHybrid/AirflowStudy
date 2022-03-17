# Template Search Path 에 대하여..

## 발단
Listing 4.20에서 `template_searchpath`를 사용하는 예시가 나오는데, 특정 확장자를 가진 템플릿 파일들을 찾게 할 수 있다는 식으로 설명이 되어있다.
jinja templating 초보 입장에서 왜 template을 이용해서 파일들의 경로 prefix를 줄 수 있는 것인지 궁금해서 찾아봤다.
~~사실 그게 아니고 이름은 `template_searchpath`인데 template로 되어있지도 않은 파일을 찾게 해준다고?! 하면서 jinja 초보답게 급발진하면서 찾아봤다..~~

(+ 궁금증에 대한 답이 대부분 책에 나와있었는데 미처 보지 못했다... :sweat_smile:)


## `template_searchpath`는 jinja를 위한 것이 맞다.
일단 [official doc](https://airflow.apache.org/docs/apache-airflow/1.10.4/_api/airflow/models/dag/index.html#airflow.models.dag.DAG)에 보면 `template_searchpath`에 대해 아래와 같이 간단한 설명을 볼 수 있다.
```
This list of folders (non relative) defines where jinja will look for your templates.
Order matters. Note that jinja/airflow includes the path of your DAG file by default.
```

하지만 이 설명은 나같은 jinja template 초보에게는 혼란만 줄 뿐이다.

일단 설명을 좀 더 덧붙이자면 (책에 나와있는 내용이다), 각 `Operator`는 `template_fields`와 `template_ext` attribute를 가지고 있다.
전자는 jinja templating을 적용할 수 있는 인자들을 명시하고 후자는 jinja templating을 적용할 수 있는 특정 파일 확장자를 명시한다.
책에 나온 `PostgresOperator`의 경우 아래와 같이 명시되어 있다.
```python
template_fields: Sequence[str] = ('sql',)
...
template_ext: Sequence[str] = ('.sql',)
```

그래서 위의 정보를 이용해서 `Operator`마다 jinja가 열심히 해당되는 field 마다 templating 해준 다음에 `Operator`에 넘겨주는 것이다.

## jinja를 활용해서 일반 파일들도 간단하게 넘겨주자
jinja가 template가 된 파일들에 대해서 열심히 templating을 적용해주고 정보를 `Operator`에 넘겨주게 되는데, 이를 활용해서 templating 되지 않은 파일은 jinja가 아무 액션도 취하지 않고 `Operator`에 넘겨주게 사용하는 것이 책의 용례이다.
~~`template_fields`와 `template_ext`에 대한 설명을 잘 읽었다면 한번에 이해했을텐데...~~

## *Order matters*. 어떻게?
맨 앞에꺼로 될 수도 있고, 마지막꺼로 overwrite 될 수 있는데 어떻다는 것인지 궁금했다.
이 부분에 대한 답은 jinja2의 FileSystemLoader [official doc](https://jinja.palletsprojects.com/en/3.0.x/api/#jinja2.FileSystemLoader)에서 찾을 수 있다.
```
A list of paths can be given. The directories will be searched in order, stopping at the first matching template.
```
라고 되어있고, airflow 소스코드를 보면 `FileSystemLoader`를 사용해서 env들을 가져오기 때문에 이렇게 동작할 거 같다.
실제로 테스트 해보니 맞다.
