from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.bash import BashOperator

default_args = {
    "owner" : "airflow",
    "retrys" : 5,
    "retry_delay" : timedelta(minutes = 2)
}

with DAG(
    
    dag_id = "new_dag",
    default_args = default_args,
    description = "this is a new dag file",
    start_date = datetime (2024, 11, 22),
    schedule_interval = "@daily"

) as dag:
    task_1st = BashOperator (
        task_id = "task_1st",
        bash_command = "echo this is the first task for this dag"
    )

    task_2nd = BashOperator (
        task_id = "task_2nd",
        bash_command = "echo this is the second task for this dag"
    )


    task_1st >> task_2nd