import time
import os
from skyfield.api import Loader, wgs84, EarthSatellite

# 1. Identity - Which satellite am I?
# We will pass these via Docker later
SAT_NAME = os.getenv("SAT_NAME", "UNKNOWN_SAT")
TLE_L1 = os.getenv("TLE_L1")
TLE_L2 = os.getenv("TLE_L2")

# 2. Setup Data Directory
data_dir = '/app/data' # Inside the container
load = Loader(data_dir)
ts = load.timescale()

if not TLE_L1 or not TLE_L2:
    print(f"[{SAT_NAME}] Error: No TLE data provided. Powering down.")
    exit(1)

sat = EarthSatellite(TLE_L1, TLE_L2, SAT_NAME, ts)

print(f"[{SAT_NAME}] Systems Online. Commencing orbit...")

try:
    while True:
        now = ts.now()
        geocentric = sat.at(now)
        subpoint = wgs84.subpoint(geocentric)
        
        # In a real swarm, this would be sent via an API or Radio
        print(f"[{SAT_NAME}] TELEMETRY | Lat: {subpoint.latitude.degrees:.2f} | Lon: {subpoint.longitude.degrees:.2f} | Alt: {subpoint.elevation.km:.1f}km")
        
        time.sleep(5) 
except KeyboardInterrupt:
    print(f"[{SAT_NAME}] Signal Lost.")