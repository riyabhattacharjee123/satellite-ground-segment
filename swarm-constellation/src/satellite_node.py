import time
import os
import math
import random
import requests
from skyfield.api import Loader, wgs84, EarthSatellite
from saliency_engine import SaliencyEngine  # AI module

# Configurations
TARGET_LAT, TARGET_LON = 49.87, 8.65
THRESHOLD_KM = 5000.0 
BASELINE_PATH = "/app/mission_data/darmstadt_training_baseline.csv"

SAT_NAME = os.getenv("SAT_NAME", "UNKNOWN_SAT")
TLE_L1 = os.getenv("TLE_L1")
TLE_L2 = os.getenv("TLE_L2")

# 1. Initialize the "AI detection engine with the baseline data"
engine = SaliencyEngine(BASELINE_PATH)
engine.train_model()

# 2. Initialize the Physics
load = Loader('/app/data')
ts = load.timescale()
sat = EarthSatellite(TLE_L1, TLE_L2, SAT_NAME, ts)

def get_distance(lat1, lon1, lat2, lon2):
    R = 6371.0 # Earth radius in km
    p1, p2 = math.radians(lat1), math.radians(lat2)
    d_lat, d_lon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(d_lat/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(d_lon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

print(f"[{SAT_NAME}] Deployment Complete. AI Engine Active.")

try:
    while True:
        now = ts.now()
        subpoint = wgs84.subpoint(sat.at(now))
        curr_lat, curr_lon = subpoint.latitude.degrees, subpoint.longitude.degrees
        current_alt = subpoint.elevation.km
        
        dist = get_distance(curr_lat, curr_lon, TARGET_LAT, TARGET_LON)
        
        # Default Payload
        payload = {
            "sat_id": SAT_NAME,
            "lat": round(curr_lat, 2),
            "lon": round(curr_lon, 2),
            "alt": round(current_alt, 1),
            "is_anomaly": False,
            "temp": None
        }

        # MISSION LOGIC: If in range, perform "Sensor Read"
        if dist <= THRESHOLD_KM:
            # Step 2.2 Simulation: Generate a temperature
            # 95% chance of normal (15C), 5% chance of anomaly (50C)
            sample_temp = 50.0 if random.random() > 0.95 else random.uniform(10, 20)
            
            # Step 3.3: Ask the AI
            is_weird = engine.analyze_reading(sample_temp)
            
            payload["temp"] = round(sample_temp, 2)
            payload["is_anomaly"] = is_weird
            
            if is_weird:
                print(f"[{SAT_NAME}] ALERT: Anomalous temp detected: {sample_temp}°C! Downlinking priority data.")
            else:
                print(f"[{SAT_NAME}] Passing Darmstadt: Normal temp ({sample_temp}°C).")

        # Send to Ground Station
        try:
            response = requests.post("http://ground-station:8000/telemetry", json=payload, timeout=2)
            if response.status_code == 422:
                print(f"[{SAT_NAME}] Schema Error: {response.json()}")
        except:
            pass
            
        time.sleep(5)
except KeyboardInterrupt:
    print("Signal Lost.")