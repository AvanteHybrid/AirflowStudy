from airflow.hooks.base import BaseHook
from airflow.models.baseoperator import BaseOperator
from airflow.utils.decorators import apply_defaults
import requests


class ElasticCustomHook(BaseHook):

    conn_type = 'elasticsearch'
    hook_name = 'ElasticCustomHook'

    def __init__(self, conn_id: str, context: dict = None):
        super().__init__(context)
        self._conn_id = conn_id
        self._session = None
        self._base_url = None

    def get_conn(self):
        if self._session is None:
            config = self.get_connection(self._conn_id)
            # schema = config.schema
            host = config.host
            port = config.port

            self._session = requests.Session()
            self._base_url = f"{config.schema}://{host}:{port}"
        return self._session, self._base_url

    def get_regions(self, end_date):
        session, base_url = self.get_conn()
        response = session.get(
            url=f"{base_url}/regions/_search",
            json={
                "query": {
                    "range": {
                        "updated_on": {
                            "lte": end_date
                        }
                    }
                }
            })
        self.log.info(response.json())
        return response


class ElasticOperator(BaseOperator):
    template_fields = ('_end_date',)
    @apply_defaults
    def __init__(self, conn_id, end_date='{{next_ds}}', **kwargs):
        super().__init__(**kwargs)
        self._conn_id = conn_id
        self._end_date = end_date

    def execute(self, context):
        hook = ElasticCustomHook(self._conn_id)

        response = hook.get_regions(self._end_date)
        self.log.info(response)

