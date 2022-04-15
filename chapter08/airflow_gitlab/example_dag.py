import airflow
from airflow import DAG
from airflow_gitlab.sensors import GitlabTagSensor
from airflow_gitlab.operators import GitlabPipelineOperator


with DAG(
    dag_id="sample_gitlab_dag",
    schedule_interval="@daily",
    start_date=airflow.utils.dates.days_ago(1),
) as dag:
    gitlab_conn_id = "GITLAB_CONNECTION"
    gitlab_project_id = "GITLAB_PROJECT_ID"
    gitlab_tag_name = "TAG_NAME"

    sensor = GitlabTagSensor(
        task_id="wait_for_tag",
        gitlab_conn_id=gitlab_conn_id,
        gitlab_project_id=gitlab_project_id,
        tag_name=gitlab_tag_name,
    )

    pipeline = GitlabPipelineOperator(
        task_id="create_pipeline",
        gitlab_conn_id=gitlab_conn_id,
        gitlab_project_id=gitlab_project_id,
        gitlab_pipeline_ref=gitlab_tag_name,
        wait_for_completion=True,
    )

    sensor >> pipeline
