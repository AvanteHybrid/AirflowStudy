# Monkeypatch
책에서는 monkeypatch를 위해서 pytest-mocker를 설치해 사용하고 있다.

그러나, 기본적인 monkeypatch 기능은 pytest 기본 패키지에서 fixture로 제공하고 있다. 물론 사용할 수 있는 범위가 매우 다르다.

## Monkeypatch의 어원
 - 처음에는 guerillapatch로 불렸다. test하면서 코드를 바꾸게 되니 심히 적절한 어원이 아닐 수 없다.
 - 사람들이 guerillapatch를 gorillapatch로 잘못 듣고, gorillapatch라는 말이 더 자주 쓰이기 시작함
 - gorillapatch는 너무 어감이 세고, 거대한 패치(수정)인 것 같은 기분을 들게 만들었기에, 같은 종이지만 더 귀여운 monkeypatch로 이름을 변경함

[출처](https://all-dev-kang.tistory.com/entry/%EA%B0%9C%EB%B0%9C%EC%A7%80%EC%8B%9D-%EB%AA%BD%ED%82%A4-%ED%8C%A8%EC%B9%98Monkey-patch%EC%97%90-%EB%8C%80%ED%95%98%EC%97%AC)

## Monkeypatch의 사용법
[document](https://docs.pytest.org/en/7.1.x/how-to/monkeypatch.html)
 - pytest-mocker의 `mocker`와 같이, monekypatch는 fixture이다.
 - 아래와 같이, test의 parameter에 monkeypatch를 넣으면, monkeypatch 기능을 사용할 수 있다.
    ```python
    def test_monkey(monkeypatch):
        ....
    ```

## 사용할 수 있는 기능
 - pytest-mock/unittest.mock과 달리, call history/input args를 알려주는 기능은 없으며, 오롯이 테스트를 위한 **환경/클래스/함수/값** 세팅/변경/삭제만이 가능하다.


```python
# object의 attr(함수, 변수)를 세팅/변경하기 위해 사용
monkeypatch.setattr(obj, name, value, raising=True)
# 모듈이름으로도 가능! 다만, 모듈이 아니라 현재 test코드에서는 사용할 수 없는 듯 함
monkeypatch.setattr("somemodule.obj.name", value, raising=True)
# object의 attr(함수, 변수)를 삭제하기 위해 사용.
monkeypatch.delattr(obj, name, raising=True)

# dictionary에서 값 세팅/변경
monkeypatch.setitem(mapping, name, value)
# dictionary에서 값 제거
monkeypatch.delitem(obj, name, raising=True)
# 환경 변수 세팅/변경
monkeypatch.setenv(name, value, prepend=None)
# 환경 변수 삭제
monkeypatch.delenv(name, raising=True)

...

```

### 예제
```python

di = {
    "hello": "there"
}

class Hello:
    say = 'typing'
    @classmethod
    def baffled(*arg,**args):
        return 'test'

def monkey(*arg, **kwargs):
    return 'testing'

def test_hello(monkeypatch):
    monkeypatch.setattr(Hello, 'baffled', monkey)
    monkeypatch.setattr(Hello, 'say', 'type')
    print(Hello().baffled())
    print(Hello().say)

def test_twice():
    print(Hello().baffled())
    print(Hello().say)

def test_3(monkeypatch):
    monkeypatch.setitem(di, 'hello', 'bye')
    print(di)

```


## unittest.mock.MagicMock
 - pytest를 사용하면서도 unittest의 mock을 사용할 수 있다.
 - unittest.mock.MagicMock은 unittest.mock.Mock의 서브클래스이다.
 - MagicMock을 통해 쉽게 python magic method들도 모킹을 할 수 있다.
 - pytest의 `monkeypatch`와 달리, 클래스/함수/값의 변경 뿐 아니라, call history/input args 등도 알려준다.

```python
class ProductionClass:
    def method(self):
        self.something(1,2,3,ela=4)
    def something(self, a, b, c, ela=2):
        pass
    def mean(self):
        return 'Anyeong'


def test_function_mocking():
    real = ProductionClass()
    real.something = MagicMock()
    real.method()
    real.method()
    print(real.something.call_count)
    print(list(real.something.call_args))


def test_variable_mocking():
    real = ProductionClass()
    mock = MagicMock()
    mock.return_value = 'hello'
    real.mean = mock

    print(real.mean())
    print(real.method())

```


 - 궁금점: unittest의 mock을 pytest에서 사용함으로써 생기는 문제는 없을까?

[출처](https://docs.python.org/ko/3/library/unittest.mock.html#unittest.mock.MagicMock)


## monkeypatch/unittest.mock/pytest-mock 비교

1. monkeypatch
    - 장점:
        - 가볍다! unittest.mock처럼 call tracking이 벌어지지 않으니까!
        - pytest말고 외부 패키지를 설치할 필요가 없다!
    - 단점:
        - fixture를 사용하기때문에, IDE에서 사용할 때 메서드들을 외워둬야 한다는 단점이 있다...
    - 적합한 usecase:
        - 단순히 function/class의 기능을 변경하고 싶을 때. 그 외의 다른 기능은 필요없을때!

2. unittest.mock
    - 장점:
        - python 3.0이후로 부터는 python에 기본으로 딸려온다.
        - monkeypatch말고도 굉장히 많은 기능이 있다!(call tracking 등)
        - IDE로 method들을 쉽게 확인할 수 있다. 예~
    - 단점:
        - call tracking 등 부수 기능이 많기 때문에 pytest monkeypatch보다는 무거울 수 있다.
        - MagicMock이 사용자가 알기 어렵게 맘대로 기능하는 부분이 있다고, 조심해야 한다고 한다. (안 사용해봐서 정확하게 뭐가 문제인지는....)
    - 적합한 usecase:
        - monkeypatch 뿐 아니라, call tracking 기능 등도 사용하고 싶을 때

3. pytest-mock
    - pytest-mock은, 사실 unittest.mock의 wrapper이다. 실제로는 unittest.mock을 쓰는 것이며, unittest.mock의 대부분의 기능을 제공한다. 다만, monkeypatch의 api를 사용할 뿐이라고..
    - 장점: monkeypatch말고도 굉장히 많은 기능이 있다.
    - 단점:
        - pytest의 외부 플러그인 이기에 별도 설치가 필요하다.
        - call tracking 등 부수 기능이 많기 때문에 pytest monkeypatch보다는 무거울 수 있다.
    - 적합한 usecase:
        - monkeypatch 뿐 아니라, call tracking 기능 등도 사용하고 싶을 때


[monkeypatch vs unittest.mock vs pytest-mock](https://github.com/pytest-dev/pytest/issues/4576#:~:text=It%20does%20seem%20to%20come%20down%20to%20personal%20preference%20as%20far%20as)