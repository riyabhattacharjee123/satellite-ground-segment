from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel
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

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "sat_id", "lat", "lon", "alt"])
    logger.info("Mission log CSV created at %s", DATA_FILE)

class Telemetry(BaseModel):
    sat_id: str
    lat: float
    lon: float
    alt: float

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    logger.info("Ground Station API is online. Listening on port 8000.")
    logger.info("Mission log file: %s", DATA_FILE)

@app.get("/")
def read_root():
    logger.info("Root endpoint hit")
    return {"message": "Ground Station API is online"}

@app.get("/health")
def health_check():
    logger.info("Health check requested - status: healthy")
    return {"status": "healthy"}

@app.post("/telemetry")
async def receive_telemetry(data: Telemetry):
    logger.info("Telemetry received from %s", data.sat_id)

    # 1. Default header in case the file is empty/missing
    header = ["timestamp", "sat_id", "lat", "lon", "alt"]
    rows = []

    # 2. Read existing data
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", newline="") as f:
                reader = list(csv.reader(f))
                if len(reader) > 0:
                    header = reader[0]
                    rows = reader[1:]
        except Exception as e:
            logger.error("Could not read log file: %s", e)

    # 3. Append and Trim
    new_entry = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), data.sat_id, data.lat, data.lon, data.alt]
    rows.append(new_entry)
    
    if len(rows) > 2500:
        rows = rows[-2500:]

    # 4. Atomic-ish Write
    try:
        with open(DATA_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)
    except Exception as e:
        logger.error("Failed to write to mission log: %s", e)

    return {"status": "success"}

if __name__ == "__main__":
    logger.info("Starting Ground Station server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)