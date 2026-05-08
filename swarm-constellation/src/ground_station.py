from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel
from typing import Optional
import os
import csv
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [GROUND-STATION] %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

DATA_FILE = "/app/data/mission_log.csv"
os.makedirs("/app/data", exist_ok=True)

# FIX 2: Updated CSV Header to include AI fields
CSV_HEADER = ["timestamp", "sat_id", "lat", "lon", "alt", "temp", "is_anomaly"]

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADER)
    logger.info("Mission log CSV created with AI headers at %s", DATA_FILE)

class Telemetry(BaseModel):
    sat_id: str
    lat: float
    lon: float
    alt: float
    is_anomaly: bool = False
    temp: Optional[float] = None

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Ground Station API is online"}

@app.post("/telemetry")
async def receive_telemetry(data: Telemetry):
    logger.info("Telemetry received from %s (Anomaly: %s)", data.sat_id, data.is_anomaly)

    rows = []
    # 1. Read existing data
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", newline="") as f:
                reader = list(csv.reader(f))
                if len(reader) > 0:
                    rows = reader[1:] # Keep data, skip header
        except Exception as e:
            logger.error("Could not read log file: %s", e)

    # 2. Prepare new entry with AI fields
    new_entry = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
        data.sat_id, 
        data.lat, 
        data.lon, 
        data.alt,
        data.temp if data.temp is not None else "", # Handle nulls
        data.is_anomaly
    ]
    
    rows.append(new_entry)
    
    # 3. Trim buffer (Last 2500 rows)
    if len(rows) > 2500:
        rows = rows[-2500:]

    # 4. Write back to file
    try:
        with open(DATA_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADER)
            writer.writerows(rows)
    except Exception as e:
        logger.error("Failed to write to mission log: %s", e)

    return {"status": "success"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)