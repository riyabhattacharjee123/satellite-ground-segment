import time
import os
import math
import random
import requests
import numpy as np
from joblib import Parallel, delayed
from skyfield.api import Loader, wgs84, EarthSatellite
from saliency_engine import SaliencyEngine  # AI module
import xarray as xr # NetCDF processing

# Paths
BASELINE_PATH = "/app/data/darmstadt_training_baseline.csv"
SENSOR_DATA_PATH = "/app/data/global_sensor_data.nc" # Our NetCDF

# Configurations
TARGET_LAT, TARGET_LON = 49.87, 8.65
THRESHOLD_KM = 5000.0
SAT_NAME = os.getenv("SAT_NAME", "UNKNOWN_SAT")
TLE_L1 = os.getenv("TLE_L1")
TLE_L2 = os.getenv("TLE_L2")


# 1. Initialize the "AI detection engine with the baseline data"
engine = SaliencyEngine(BASELINE_PATH)
engine.train_model()

# Load the NetCDF into memory
# We use 'decode_times=True' to handle the time dimension   
try:
    earth_data = xr.open_dataset(SENSOR_DATA_PATH)
    print(f"[{SAT_NAME}] Sensor Array Online. NetCDF Loaded.")
except Exception as e:
    print(f"[{SAT_NAME}] CRITICAL: Could not load NetCDF: {e}")
    earth_data = None

# 2. Initialize the Physics
load = Loader('/app/data')
ts = load.timescale()
sat = EarthSatellite(TLE_L1, TLE_L2, SAT_NAME, ts)

def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)
    a = np.sin(delta_phi / 2.0)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2.0)**2
    c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
    return R * c

def evaluate_single_coordinate(lat, lon, target_lat, target_lon, threshold_km):
    distance = calculate_haversine_distance(lat, lon, target_lat, target_lon)
    return distance <= threshold_km

def parallel_grid_search(lat_array, lon_array, target_lat, target_lon, threshold_km):
    flat_lats = lat_array.flatten()
    flat_lons = lon_array.flatten()
    results = Parallel(n_jobs=-1)(
        delayed(evaluate_single_coordinate)(lat, lon, target_lat, target_lon, threshold_km)
        for lat, lon in zip(flat_lats, flat_lons)
    )
    return np.array(results).reshape(lat_array.shape)

print(f"[{SAT_NAME}] Deployment Complete. AI Engine Active.")

try:
    while True:
        now = ts.now()
        subpoint = wgs84.subpoint(sat.at(now))
        curr_lat, curr_lon = subpoint.latitude.degrees, subpoint.longitude.degrees
        current_alt = subpoint.elevation.km
        
        dist = calculate_haversine_distance(curr_lat, curr_lon, TARGET_LAT, TARGET_LON)
        
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
            # 3. SAMPLE THE NETCDF (The Digital Twin Sensor)
            # We use .sel() with method='nearest' to find the closest pixel to our orbit
            try:
                # Selecting the LST (Land Surface Temperature) at our current location
                reading = earth_data.lst.sel(
                    lat=curr_lat, 
                    lon=curr_lon, 
                    method="nearest"
                ).values[0] # [0] because it's a 1-item array
            
                # Step 3.3: Ask the AI
                is_weird = engine.analyze_reading(reading)
                
                payload["temp"] = round(float(reading), 2)
                payload["is_anomaly"] = is_weird
                
                if is_weird:
                    print(f"[{SAT_NAME}] ALERT: Anomalous temp detected: {reading}°C! Downlinking priority data.")
                else:
                    print(f"[{SAT_NAME}] Passing Darmstadt: Normal temp ({reading}°C).")

            except Exception as e:
                print(f"[{SAT_NAME}] Sensor Read Failed: {e}")


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