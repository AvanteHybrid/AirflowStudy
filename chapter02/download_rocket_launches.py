import json
import pathlib

import airflow
import requests
import requests.exceptions as requests_exceptions
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator


# Initiating a DAG object is the starting point of any workflow.
dag = DAG(
    dag_id="download_rocket_launches",  # name of the DAG
    start_date=airflow.utils.dates.days_ago(14),  # The date of first run
    schedule_interval=None,  # DAG running interval
)

# First task definition.
# Apply bash to download the URL response.
download_launches = BashOperator(
    task_id="download_launches",  # name of the task
    bash_command="curl -o /tmp/launches.json -L  \
    'https://ll.thespacedevs.com/2.0.0/launch/upcoming'",  # command to execute
    dag=dag,  # reference to the dag the task is attached to, so that Airflow knows which tasks belong to which DAG.
)


def _get_pictures():
    # Ensure directory exists
    pathlib.Path("/tmp/images").mkdir(parents=True, exist_ok=True)

    # Download all pictures in launches.json
    with open("/tmp/launches.json") as f:
        launches = json.load(f)
        image_urls = [launch["image"] for launch in launches["results"]]
        for image_url in image_urls:
            try:
                response = requests.get(image_url)
                image_filename = image_url.split("/")[-1]
                target_file = f"/tmp/images/{image_filename}"

                with open(target_file, "wb") as f:
                    f.write(response.content)
                print(f"Downloaded {image_url} to {target_file}")

            except requests_exceptions.MissingSchema:
                print(f"{image_url} appears to be an invalid URL.")
            
            except requests_exceptions.ConnectionError:
                print(f"Could not connect to {image_url}.")


# Another task definition calling Python function to download images.
get_pictures = PythonOperator(
    task_id="get_pictures",
    python_callable=_get_pictures,
    dag=dag
)

# Another task definition executing bash command to notify.
notify = BashOperator(
    task_id="notify",
    bash_command='echo "There are now $(ls /tmp/images/ | wc -l) images."',
    dag=dag,
)

# Set the order of task execution.
download_launches >> get_pictures >> notify