import pickle
import time
from typing import Any, Callable, Optional

from airflow import AirflowException
from airflow.models import BaseOperator
from airflow.utils.context import Context
from gitlab import GitlabError
from gitlab.v4.objects import ProjectManager

from airflow_gitlab.hooks import GitlabHook


def _is_picklable(obj):
    try:
        pickle.dumps(obj)

    except pickle.PicklingError:
        return False
    return True


class GitlabOperator(BaseOperator):
    template_fields = ("gitlab_method_args",)

    def __init__(
        self,
        gitlab_conn_id: str,
        gitlab_project_id: str,
        gitlab_method: str = None,
        gitlab_method_args: Optional[dict] = None,
        result_processor: Optional[Callable] = None,
        **kwargs,
    ) -> None:
        """
        GitlabOperator to interact and perform action on Gitlab project API.
        This operator is designed to use python-gitlab: https://python-gitlab.readthedocs.io/en/stable/

        Referenced from https://github.com/apache/airflow/blob/main/airflow/providers/github/operators/github.py
        """
        super().__init__(**kwargs)
        self.gitlab_conn_id = gitlab_conn_id
        self.gitlab_project_id = gitlab_project_id
        self.method_name = gitlab_method
        self.gitlab_method_args = gitlab_method_args
        self.result_processor = result_processor

    def execute(self, context: Context) -> Any:
        try:
            hook = GitlabHook(gitlab_conn_id=self.gitlab_conn_id)
            client = hook.get_conn()
            result = resource = client.projects.get(self.gitlab_project_id)
            if self.method_name:
                result = getattr(resource, self.method_name)(**self.gitlab_method_args)
            if self.result_processor:
                return self.result_processor(result)
            if _is_picklable(result):
                return result
            return

        except GitlabError as gitlab_error:
            raise AirflowException(
                f"Failed to execute GitlabOperator, error: {gitlab_error}"
            )
        except Exception as e:
            raise AirflowException(f"Gitlab operator error: {str(e)}")


class GitlabPipelineOperator(GitlabOperator):
    def __init__(
        self,
        gitlab_conn_id: str,
        gitlab_project_id: str,
        gitlab_pipeline_ref: str,
        gitlab_pipeline_variables: Optional[dict] = None,
        wait_for_completion: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(
            gitlab_conn_id=gitlab_conn_id,
            gitlab_project_id=gitlab_project_id,
            result_processor=self._create_pipeline,
            **kwargs,
        )
        self.gitlab_pipeline_ref = gitlab_pipeline_ref
        self.gitlab_pipeline_variables = gitlab_pipeline_variables
        self.wait_for_completion = wait_for_completion

    def _create_pipeline(self, project: ProjectManager):
        variables = []
        if self.gitlab_pipeline_variables:
            for key, value in self.gitlab_pipeline_variables:
                variables.append({"key": key, "value": value})
        pipeline = project.pipelines.create(
            {"ref": self.gitlab_pipeline_ref, "variables": variables}
        )
        if not self.wait_for_completion:
            return
        # wait for pipeline completion
        for pipeline_job in pipeline.jobs.list():
            project_job = project.jobs.get(pipeline_job.id)
            # wait for job completion
            while project_job.finished_at is None:
                project_job.refresh()
                time.sleep(1)
            if project_job.status != "success":
                raise AirflowException(f"Gitlab pipeline failed: {project_job.web_url}")
        return
