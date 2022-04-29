# About Kubernetes Objects
K8S 초급자로서, 책에 있는 예제에 나온 K8S 리소스 명세에 대해서 좀 더 구체적으로 알면 좋을 것 같아 일부 정리하였다.
K8S object들은 각각 매우 복잡한 spec들을 가지고 있지만, 책에서 나오거나 아주 기초적인 것들만 가져왔다.

## Kubernetes Objects
책에서 yml 파일을 가지고 스토리지 리소스 명세를 작성하고 API 배포를 위한 명세를 작성하여 원하는 K8S의 리소스를 사용하게 된다.
각각의 명세는 Kubernetes Object를 생성하기 위함이라고 할 수 있고, Object들을 명세된 state 대로 생성하고 유지하는 것이 K8S가 하는 역할이다.

Kubernetes Object의 종류에는 크게 두가지가 있다:
1. 다른 Object가 관여할 필요없이 independent 하게 존재하는 Object
e.g., Pod, Service, Volume, Namespace, etc.
2. 위 Objects들 위에 존재하는 High-level objects (controllers)
e.g., Deployment, Replication Controller, ReplicaSets, etc.

각각의 Object는 `spec`과 `status`라는 두가지 property를 가진다.
* `spec`: Object에 대한 명세를 나타낸다.
* `status`: Object의 현재 state를 나타내고, 실시간으로 K8S control plane에 의해 업데이트 된다.

### Required Fields for Object Configuration
1. `apiVersion`: K8S API의 어떤 버전을 사용하여 Object를 생성할 것인지 나타낸다.
2. `kind`: Object의 타입을 지정한다. Pod, Deployment 등이 그 중 하나가 들어가게 된다.
3. `metadata`: Object에 대한 메타데이터를 포함한다. `name`, `UID` 등 object를 식별하기 위해서 사용한다.
4. `spec`: Object의 desired state에 대한 명세가 들어간다. Pod의 경우 어떤 container image를 사용할 지 등이 될 것이다.

## Storage Resource Definition
책에서 나온 PersistentVolume (PV)과 PersistentVolumeClaim (PVC)에 대해서 살펴보자.

PV는 K8S 클러스터 관리자가 생성한 volume으로써, Pod 등이 사용할 수 있도록 확보해둔 스토리지 리소스다.
호스트의 물리 디스크를 가상화한 것의 일종이라고 생각할 수 있겠다.
PVC는 사용자가 스토리지를 사용하기 위해서 PV에 요청하는 것을 명세한다.
Pod의 컨테이너는 호스트의 볼륨을 사용하기 위해서 PVC를 이용해야 한다.

### PV Specification
* `spec.capacity.storage`: 용량 설정. (e.g., 2Gi, 10Gi..)
* `spec.volumeMode`: 볼륨을 어떤 방식으로 사용할 지 (`Filesystem` or `Block`)
* `spec.accessModes`: 접근 모드 선택. (`ReadWriteOnce`, `ReadOnlyMany`, `ReadWriteMany`, `ReadWriteOncePod`)
* `spec.storageClassName`: PVC와 연결할 때 사용되는 클래스 이름.
* `hostPath`: 호스트와 연결될 파일 경로

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-example
spec:
  capacity:
    storage: 10Gi
  volumeMode: Filesystem
  accessModes:
  - ReadWriteOnce
  storageClassName: manual
  hostPath: path: /tmp/log
```

### PVC Specification
* `spec.storageClassName`: 연결될 PV의 클래스 이름
* `spec.accessModes`: 스토리지 할당에 허용되는 접근 모드
* `spec.resources.requests.storage`: 요청할 스토리지 크기

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc-example
spec:
  storageClassName: manual
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

## Deployment and Service Definition
Deployment란, 동일한 pod 들을 유지하면서, 이들이 설정된 config대로 존재할 수 있게하는 Kubernetes Object이다.
Service란, K8S 클러스터 내에 네트워크를 명세한다. Virtual IP를 부여하는 것과 비슷하다.

### Pod vs Deployment
개인적으로 Pod와 Deployment는 언제 어떻게 사용되면 좋을지 궁금해서 찾아봤다.

#### Pod
* 한개의 컨테이너 집합을 실행시킨다.
* 일회성으로 job을 수행하고 싶을 때 좋다.
* Production에서는 사용되는 경우가 드물다.

#### Deployment
* 동일한 pod들을 여러개 실행시킨다.
* 각각의 pod를 모니터링하고 업데이트 해준다.
* Develop, Production에 용이하다.

### Deployment Specification
* `spec.replicas`: 몇개의 replicated Pod를 생성할 지
* `spec.selector`: Deployment가 어떤 Pod를 관리할 지 찾아낼 때 사용하는 명세
* `spec.template`: Pod 생성을 위한 정보들. `spec`에는 Pod의 spec이 들어간다.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: movielens-deployment
  labels:
    app: movielens
spec:
  replicas: 1
  selector:
    matchLabels:
      app: movielens
  template:
    metadata:
      labels:
        app: movielens
    spec:
      containers:
      - name: movielens
        image: manning-airflow/movielens-api:latest
        imagePullPolicy: Never
        ports:
        - containerPort: 5000
        env:
        - name: API_USER
          value: airflow
        - name: API_PASSWORD
          value: airflow
```

### Service Specification
* `spec.selector`: 연결하기 위한 Pod를 찾을 때 사용
* `spec.ports`: 어떤 포트를 어떻게 매핑할 지

```yaml
apiVersion: v1
kind: Service
metadata:
  name: movielens
spec:
  selector:
    app: movielens
  ports:
    - protocol: TCP
      port: 80
      targetPort: 5000
```


References:
* https://www.containiq.com/post/kubernetes-objects
* https://kubernetes.io/docs/concepts/storage/persistent-volumes/
* https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
* https://kubernetes.io/docs/concepts/workloads/pods/