from typing import Optional

from gitlab import Gitlab as GitlabClient

from airflow.hooks.base import BaseHook


class GitlabHook(BaseHook):
    # conn_name_attr = "gitlab_conn_id"
    # default_conn_name = "gitlab_default"
    # conn_type = "gitlab"
    # hook_name = "Gitlab"

    def __init__(self, gitlab_conn_id: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.gitlab_conn_id = gitlab_conn_id
        self.client: Optional[GitlabClient] = None
        self.get_conn()

    def get_conn(self) -> GitlabClient:
        if self.client is not None:
            return self.client

        conn = self.get_connection(self.gitlab_conn_id)
        access_token = conn.password
        url = f"{conn.schema}://{conn.host}"
        self.client = GitlabClient(url=url, private_token=access_token)
        self.client.auth()
        return self.client
