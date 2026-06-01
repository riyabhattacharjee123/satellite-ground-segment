from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys

# Give Airflow access to our generator scripts
sys.path.append('/opt/airflow/scripts')

def refresh_sensor_data():
    # In a real mission, this would call a NASA/ESA API to pull fresh data.
    # For now, we regenerate our synthetic NetCDF file.
    from generate_sensor_data import generate_synthetic_lst_with_anomaly
    generate_synthetic_lst_with_anomaly()
    print("Mission Control: NetCDF Sensor Data Refreshed.")

default_args = {
    'owner': 'mission_control',
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'satellite_sensor_ingestion',
    default_args=default_args,
    schedule_interval='@hourly',
    catchup=False,
    description='Refreshes the global NetCDF sensor map every hour for the satellite constellation.'
) as dag:

    update_sensors = PythonOperator(
        task_id='refresh_netcdf_data',
        python_callable=refresh_sensor_data
    )
