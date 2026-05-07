import time
import os
import requests # This is the "phone" the satellite uses to call home
from skyfield.api import Loader, wgs84, EarthSatellite

SAT_NAME = os.getenv("SAT_NAME", "UNKNOWN_SAT")
TLE_L1 = os.getenv("TLE_L1")
TLE_L2 = os.getenv("TLE_L2")

data_dir = '/app/data'
load = Loader(data_dir)
ts = load.timescale()

sat = EarthSatellite(TLE_L1, TLE_L2, SAT_NAME, ts)

print(f"[{SAT_NAME}] Systems Online. Commencing orbit...")

try:
    while True:
        now = ts.now()
        geocentric = sat.at(now)
        subpoint = wgs84.subpoint(geocentric)
        
        # 1. Prepare the data packet
        payload = {
            "sat_id": SAT_NAME,
            "lat": round(subpoint.latitude.degrees, 2),
            "lon": round(subpoint.longitude.degrees, 2),
            "alt": round(subpoint.elevation.km, 1)
        }

        # 2. Try to send it to the Ground Station
        try:
            # 'ground-station' is the name we gave in docker-compose
            response = requests.post("http://ground-station:8000/telemetry", json=payload, timeout=2)
            print(f"[{SAT_NAME}] Sent telemetry to Ground Station. Status: {response.status_code}")
        except Exception as e:
            print(f"[{SAT_NAME}] Ground Station unreachable.")
        
        time.sleep(5) 
except KeyboardInterrupt:
    print(f"[{SAT_NAME}] Signal Lost.")