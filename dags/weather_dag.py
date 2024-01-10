from airflow import DAG
from datetime import timedelta, datetime
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.task_group import TaskGroup
from airflow.providers.postgres.operators.postgres import PostgresOperator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 8),
    'email': ['myemail@domain.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=2)
}

with DAG('weather_dag_2',
        default_args=default_args,
        schedule_interval = '@daily',
        catchup=False) as dag:

        start_pipeline = DummyOperator(
            task_id = 'tsk_start_pipeline'
        )

        with TaskGroup(group_id = 'group_a', tooltip= "Extract_from_S3_and_weatherapi") as group_A:
            create_table_1 = PostgresOperator(
                task_id='tsk_create_table_1',
                postgres_conn_id = "postgres_conn",
                sql= '''  
                    CREATE TABLE IF NOT EXISTS city_look_up (
                    city TEXT NOT NULL,
                    state TEXT NOT NULL,
                    census_2020 numeric NOT NULL,
                    land_Area_sq_mile_2020 numeric NOT NULL                    
                );
                '''
            )

            truncate_table = PostgresOperator(
                task_id='tsk_truncate_table',
                postgres_conn_id = "postgres_conn",
                sql= ''' TRUNCATE TABLE city_look_up;
                    '''
            )

            uploadS3_to_postgres  = PostgresOperator(
                task_id = "tsk_uploadS3_to_postgres",
                postgres_conn_id = "postgres_conn",
                sql = "SELECT aws_s3.table_import_from_s3('city_look_up', '', '(format csv, DELIMITER '','', HEADER true)', 's3-bucket-weather-api', 'us_city.csv', 'us-east-1');"
            )

            create_table_1>>truncate_table>>uploadS3_to_postgres
        start_pipeline>>group_A
