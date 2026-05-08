import time
import os
import requests # This is the "phone" the satellite uses to call home
from skyfield.api import Loader, wgs84, EarthSatellite
import math

SAT_NAME = os.getenv("SAT_NAME", "UNKNOWN_SAT")
TLE_L1 = os.getenv("TLE_L1")
TLE_L2 = os.getenv("TLE_L2")

# Target Coordinates: Darmstadt, Germany (Mission Center / Ground Station Location)
TARGET_LAT = 49.87
TARGET_LON = 8.65
THRESHOLD_KM = 5000.0  # Reach-zone radius in kilometers

data_dir = '/app/data'
load = Loader(data_dir)
ts = load.timescale()

sat = EarthSatellite(TLE_L1, TLE_L2, SAT_NAME, ts)

def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    """
    Computes the great-circle distance between two points on a sphere 
    using the Haversine formula. Returns distance in kilometers.
    """
    R = 6371.0  # Average radius of the Earth in km
    
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

print(f"[{SAT_NAME}] Systems Online. Commencing orbit...")

try:
    while True:
        now = ts.now()
        geocentric = sat.at(now)
        subpoint = wgs84.subpoint(geocentric)
        
        current_lat = round(subpoint.latitude.degrees, 2)
        current_lon = round(subpoint.longitude.degrees, 2)
        current_alt = round(subpoint.elevation.km, 1)

        # Calculate orbital distance to our target area (Darmstadt)
        distance_to_target = round(calculate_haversine_distance(
            current_lat, current_lon, TARGET_LAT, TARGET_LON
        ), 1)

        # Evaluate if we are within the coverage/sensing window
        is_target_in_range = distance_to_target <= THRESHOLD_KM


        # 1. Prepare the data packet
        payload = {
            "sat_id": SAT_NAME,
            "lat": current_lat,
            "lon": current_lon,
            "alt": current_alt
        }

        # 2. Downlink log printout
        if is_target_in_range:
            print(f"[{SAT_NAME}] !!! ACCESS WINDOW !!! Over Darmstadt | Distance: {distance_to_target} km | Triggering sensor read...")
        else:
            print(f"[{SAT_NAME}] Normal Orbiting | Distance to Darmstadt: {distance_to_target} km")

        # 3. Try to transmit data to Ground Station
        try:
            response = requests.post("http://ground-station:8000/telemetry", json=payload, timeout=2)
            # Log the status of transmission
        except Exception as e:
            print(f"[{SAT_NAME}] Ground Station unreachable.")
        
        time.sleep(5) 
except KeyboardInterrupt:
    print(f"[{SAT_NAME}] Signal Lost.")