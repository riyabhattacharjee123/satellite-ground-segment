from fastapi import FastAPI, HTTPException
import uvicorn
from pydantic import BaseModel
from typing import Optional
import os
import csv
import logging
import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [GROUND-STATION] %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = "postgresql://mission_user:space_password@db:5432/mission_telemetry"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TelemetryRecord(Base):
    __tablename__ = "telemetry"
    id = Column(Integer, primary_key=True, index=True)
    sat_id = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    lat = Column(Float)
    lon = Column(Float)
    alt = Column(Float, nullable=True)
    temp = Column(Float, nullable=True)
    is_anomaly = Column(Boolean, default=False)

# CSV backup setup
DATA_FILE = "/app/data/mission_log.csv"
CSV_HEADER = ["timestamp", "sat_id", "lat", "lon", "alt", "temp", "is_anomaly"]
os.makedirs("/app/data", exist_ok=True)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADER)
    logger.info("Mission log CSV created at %s", DATA_FILE)

class Telemetry(BaseModel):
    sat_id: str
    lat: float
    lon: float
    alt: float
    is_anomaly: bool = False
    temp: Optional[float] = None

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)
    logger.info("Ground Station API is online. Listening on port 8000.")
    logger.info("Database tables ready.")

@app.get("/")
def read_root():
    return {"message": "Ground Station API is online"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/health/stats")
def get_stats():
    db = SessionLocal()
    try:
        total = db.query(TelemetryRecord).count()
        anomalies = db.query(TelemetryRecord).filter(TelemetryRecord.is_anomaly == True).count()
        return {
            "total_pings": total,
            "anomalies_detected": anomalies,
            "system_status": "nominal"
        }
    except Exception as e:
        logger.error("Stats query failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post("/telemetry")
async def receive_telemetry(data: Telemetry):
    logger.info("Telemetry received from %s (Anomaly: %s)", data.sat_id, data.is_anomaly)

    # Write to PostgreSQL
    db = SessionLocal()
    try:
        record = TelemetryRecord(
            sat_id=data.sat_id,
            lat=data.lat,
            lon=data.lon,
            alt=data.alt,
            temp=data.temp,
            is_anomaly=data.is_anomaly
        )
        db.add(record)
        db.commit()
        logger.info("Telemetry from %s written to database.", data.sat_id)
    except Exception as e:
        db.rollback()
        logger.error("Database write failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

    # Write to CSV as backup
    rows = []
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", newline="") as f:
                reader = list(csv.reader(f))
                if reader:
                    rows = reader[1:]
        except Exception as e:
            logger.error("Could not read CSV log: %s", e)

    rows.append([
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data.sat_id, data.lat, data.lon, data.alt,
        data.temp if data.temp is not None else "",
        data.is_anomaly
    ])

    if len(rows) > 2500:
        rows = rows[-2500:]

    try:
        with open(DATA_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADER)
            writer.writerows(rows)
    except Exception as e:
        logger.error("CSV backup write failed: %s", e)

    return {"status": "recorded", "sat_id": data.sat_id}

if __name__ == "__main__":
    logger.info("Starting Ground Station server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
