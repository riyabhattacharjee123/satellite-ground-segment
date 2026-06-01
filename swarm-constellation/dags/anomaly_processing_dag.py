from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import create_engine
import os

DATABASE_URL = "postgresql://mission_user:space_password@db:5432/mission_telemetry"
EXPORT_PATH = "/opt/airflow/mission_data/retraining_payload.csv"

def extract_and_clean_anomalies():
    print("Connecting to Ground Segment Database...")
    engine = create_engine(DATABASE_URL)

    query = "SELECT timestamp, sat_id, lat, lon, temp FROM telemetry WHERE is_anomaly = True;"
    df = pd.read_sql(query, con=engine)

    if df.empty:
        print("No anomalies found in the current tracking window.")
        return

    print(f"Found {len(df)} anomaly rows. Cleaning and deduplicating...")

    # Drop rows with missing coordinates or temperature
    df = df.dropna(subset=['lat', 'lon', 'temp'])

    # Keep the highest temperature reading per coordinate zone
    df['lat_round'] = df['lat'].round(1)
    df['lon_round'] = df['lon'].round(1)
    df_cleaned = (
        df.sort_values('temp', ascending=False)
          .drop_duplicates(subset=['lat_round', 'lon_round'])
          .drop(columns=['lat_round', 'lon_round'])
    )

    os.makedirs(os.path.dirname(EXPORT_PATH), exist_ok=True)
    df_cleaned.to_csv(EXPORT_PATH, index=False)
    print(f"Retraining payload saved to {EXPORT_PATH} ({len(df_cleaned)} rows)")

default_args = {
    'owner': 'mission_control',
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

with DAG(
    'mlops_anomaly_processing',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
    description='Extracts anomalous telemetry from the database and builds a retraining payload for the AI model.'
) as dag:

    process_anomalies = PythonOperator(
        task_id='extract_clean_anomalies',
        python_callable=extract_and_clean_anomalies
    )
