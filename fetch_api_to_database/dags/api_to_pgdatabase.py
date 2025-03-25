from airflow import DAG
from airflow.providers.http.hooks.http import HttpHook
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.decorators import task
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
import requests
import json


# CONNECTIONS ==>
#
# connection_id = 'postgres_default_2', connection_type = 'postgres', host = 'postgres', post = 5432, login = 'airflow', password = 'airflow', Database = 'airflow'.
#
# connection_id = 'attendance_api', connection_type = 'http', host = 'lucid.nassa.com.bd' (not required), login = 'airflow', password = 'airflow'.


POSTGRES_CONN_ID='postgres_default_2'
API_CONN_ID='attendance_api'

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=60),
}

## DAG
with DAG(
    dag_id='api_to_postgresql_2',
         default_args=default_args,
         description = "this is a DAG for fetching attendane data from api and storing into postgresql",
         start_date = datetime (2024, 11, 22),
         schedule_interval='@daily',
         catchup=False
         ) as dags:
    
    @task()
    def extract_attendance_data():
        """Extract weather data from Open-Meteo API using Airflow Connection."""

        # Use HTTP Hook to get connection details from Airflow connection

        http_hook=HttpHook(http_conn_id=API_CONN_ID,method='GET')

        ## Build the API endpoint
        endpoint=f'api/Attendance/GetEmployeeAttendanceTodayv2'

        ## Make the request via the HTTP Hook
        response=http_hook.run(endpoint)

        if response.status_code == 200:
            attendance_data = response.json()
            return attendance_data
        else:
            raise Exception(f"Failed to fetch attendance data: {response.status_code}")
        
    @task()
    def transform_attendance_data(attendance_data):
        """Transform the extracted attendance data."""
        # current_weather = weather_data['current_weather']
        transformed_data = []
        for record in attendance_data:
            transformed_data.append({
                'company_name': record['CompanyName'],
                'company_address': record['CompanyAddress'],
                'employee_name': record['EmployeeName'],
                'department': record['Department'],
                'designation': record['Designation'],
                'mobile': record['Mobile'],
                'email': record['Email'],
                'company_id': record['CompanyId'],
                'fromdate': record['FromDate'],
                'todate': record['ToDate'],
                'total_minutes': record['TotalMinutes'],
                'employee_id': record['EmployeeId'],
                'date': record['Date'],
                'in_time': record['InTime'],
                'out_time': record['OutTime'],
                'status': record['Status'],
                'total_hours': record['TotalHours'],
                'total_shift_hours': record['TotalShiftHours'],
                'in_datetime': record['InDatetime'],
                'out_datetime': record['OutDatetime'],
                'work_outside_status': record['WorkOutSideStatus'],
                'work_outside_location': record['WorkOutSideLocation'],
                'work_outside_remark': record['WorkOutSideRemarks'],
                'short_leave': record['ShortLeave'],
                'is_generatesalary': record['IsGenerateSalary'],
                'lastpunchtype': record['LastPunchType']
            })

        return transformed_data
    
    @task()
    def load_attendance_data(transformed_data):
        """Load transformed data into PostgreSQL."""
        pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
        conn = pg_hook.get_conn()
        cursor = conn.cursor()

        # Create table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance_data (
                company_name TEXT,
                company_address TEXT,
                employee_name TEXT,
                department TEXT,
                designation TEXT,
                mobile TEXT,
                email TEXT,
                company_id TEXT,
                from_date TEXT,
                to_date TEXT,
                total_minutes TEXT,
                employee_id TEXT,
                date TEXT,
                in_time TEXT,
                out_time TEXT,
                status TEXT,
                total_hours TEXT,
                total_shift_hours TEXT,
                in_datetime TEXT,
                out_datetime TEXT,
                work_outside_status TEXT,
                work_outside_location TEXT,
                work_outside_remarks TEXT,
                short_leave TEXT,
                is_generate_salary TEXT,
                last_punch_type TEXT
        );
        """)


        for record in transformed_data:
        # Insert transformed data into the table
            cursor.execute("""
            INSERT INTO attendance_data (
                        company_name, 
                        company_address, 
                        employee_name, 
                        department, 
                        designation, 
                        mobile,
                        email, 
                        company_id, 
                        from_date, 
                        to_date, 
                        total_minutes, 
                        employee_id,
                        date, 
                        in_time, 
                        out_time, 
                        status, 
                        total_hours, 
                        total_shift_hours,
                        in_datetime, 
                        out_datetime, 
                        work_outside_status, 
                        work_outside_location, 
                        work_outside_remarks, 
                        short_leave,
                        is_generate_salary, 
                        last_punch_type
                        )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                
                record.get('company_name'),
                record.get('company_address'),
                record.get('employee_name'),
                record.get('department'),
                record.get('designation'),
                record.get('mobile'),
                record.get('email'),
                record.get('company_id'),
                record.get('fromdate'),
                record.get('todate'),
                record.get('total_minutes'),
                record.get('employee_id'),
                record.get('date'),
                record.get('in_time'),
                record.get('out_time'),
                record.get('status'),
                record.get('total_hours'),
                record.get('total_shift_hours'),
                record.get('in_datetime'),
                record.get('out_datetime'),
                record.get('work_outside_status'),
                record.get('work_outside_location'),
                record.get('work_outside_remark'),
                record.get('short_leave'),
                record.get('is_generatesalary'),
                record.get('lastpunchtype')
            ))

        conn.commit()
        cursor.close()
        conn.close()

    ## DAG Worflow- ETL Pipeline
    weather_data= extract_attendance_data()
    transformed_data=transform_attendance_data(weather_data)
    load_attendance_data(transformed_data)