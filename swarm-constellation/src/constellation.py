import time
import os
from skyfield.api import Loader, wgs84, EarthSatellite

# 1. Point to our data directory
data_dir = os.path.join(os.getcwd(), '..', 'data')
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

load = Loader(data_dir)
ts = load.timescale()

# 2. Define our Swarm
swarm_data = [
    {"id": "SAT-01", "l1": "1 25544U 98067A   26126.52495471  .00016717  00000-0  10270-3 0  9011", "l2": "2 25544  51.6442  20.5153 0004445 220.3102 210.3102 15.48815327306221"},
    {"id": "SAT-02", "l1": "1 25544U 98067A   26126.52495471  .00016717  00000-0  10270-3 0  9011", "l2": "2 25544  51.6442  40.5153 0004445 220.3102 210.3102 15.48815327306221"},
    {"id": "SAT-03", "l1": "1 25544U 98067A   26126.52495471  .00016717  00000-0  10270-3 0  9011", "l2": "2 25544  51.6442  60.5153 0004445 220.3102 210.3102 15.48815327306221"}
]

print("Starting Virtual Swarm Propagator...")

# 3. Continuous Loop (The Live Simulation)
try:
    while True:
        now = ts.now()
        os.system('clear') # Clears the terminal screen for a clean view
        print(f"--- Swarm Telemetry | {now.utc_strftime()} ---")
        
        for entry in swarm_data:
            sat = EarthSatellite(entry['l1'], entry['l2'], entry['id'], ts)
            geocentric = sat.at(now)
            subpoint = wgs84.subpoint(geocentric)
            
            print(f"[{sat.name}] Lat: {subpoint.latitude.degrees:>7.2f} | Lon: {subpoint.longitude.degrees:>7.2f} | Alt: {subpoint.elevation.km:.1f}km")
        
        time.sleep(2) # Update every 2 seconds
except KeyboardInterrupt:
    print("\nMission Paused. Swarm entering standby.")