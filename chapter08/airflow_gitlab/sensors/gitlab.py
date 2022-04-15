from typing import Callable, Optional

from airflow.sensors.base import BaseSensorOperator
from airflow.utils.context import Context
from gitlab.v4.objects import ProjectManager

from airflow_gitlab.operators import GitlabOperator


class GitlabSensor(BaseSensorOperator):
    def __init__(
        self,
        gitlab_conn_id: str,
        gitlab_project_id: str,
        gitlab_method: str = None,
        gitlab_method_args: Optional[dict] = None,
        result_processor: Optional[Callable] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.gitlab_operator = GitlabOperator(
            task_id=f"{self.task_id}_operator",
            gitlab_conn_id=gitlab_conn_id,
            gitlab_project_id=gitlab_project_id,
            gitlab_method=gitlab_method,
            gitlab_method_args=gitlab_method_args,
            result_processor=result_processor,
        )

    def poke(self, context: "Context"):
        return self.gitlab_operator.execute(context=context)


class GitlabTagSensor(GitlabSensor):
    def __init__(
        self, gitlab_conn_id: str, gitlab_project_id: str, tag_name: str, **kwargs
    ):
        super().__init__(
            gitlab_conn_id=gitlab_conn_id,
            gitlab_project_id=gitlab_project_id,
            result_processor=self._check_tags,
            **kwargs,
        )
        self.tag_name = tag_name

    def _check_tags(self, project: ProjectManager):
        return self.tag_name in project.tags.list()
