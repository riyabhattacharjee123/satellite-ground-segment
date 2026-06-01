import xarray as xr
import numpy as np
import pandas as pd
import os
from joblib import Parallel, delayed

OUTPUT_PATH = "mission_data/global_sensor_data.nc"
TARGET_LAT, TARGET_LON = 49.87, 8.65  # Darmstadt

def process_single_coordinate_slice(lat_val, lon_val, target_lat, target_lon):
    # Returns True if this pixel is within the 2-degree anomaly radius
    distance_sq = (lat_val - target_lat) ** 2 + (lon_val - target_lon) ** 2
    return distance_sq < 4.0

def build_anomaly_mask_parallel(lat_mesh, lon_mesh, target_lat, target_lon):
    print("Launching multi-core parallel grid computation...")
    flat_lats = lat_mesh.flatten()
    flat_lons = lon_mesh.flatten()

    # Distribute across all available CPU cores
    results = Parallel(n_jobs=-1)(
        delayed(process_single_coordinate_slice)(lat, lon, target_lat, target_lon)
        for lat, lon in zip(flat_lats, flat_lons)
    )

    return np.array(results).reshape(lat_mesh.shape)

def generate_synthetic_lst_with_anomaly():
    print("Generating Global Sensor Map with Darmstadt Heatwave...")

    lats = np.linspace(-90, 90, 180)
    lons = np.linspace(-180, 180, 360)
    times = pd.date_range("2024-05-11", periods=1)

    lat_mesh, lon_mesh = np.meshgrid(lats, lons, indexing='ij')

    # Base climate: warm at equator, cold at poles
    base_temp = 30 * np.cos(np.radians(lat_mesh))

    # Build the anomaly mask in parallel across all CPU cores
    anomaly_mask = build_anomaly_mask_parallel(lat_mesh, lon_mesh, TARGET_LAT, TARGET_LON)

    # Inject 50C heatwave at Darmstadt, normal climate everywhere else
    final_temp = np.where(
        anomaly_mask,
        50.0,
        base_temp + np.random.normal(0, 1, base_temp.shape)
    )

    ds = xr.Dataset(
        data_vars=dict(lst=(["time", "lat", "lon"], final_temp[np.newaxis, :, :])),
        coords=dict(time=times, lat=lats, lon=lons),
    )

    ds.to_netcdf(OUTPUT_PATH, engine='scipy')
    print(f"Success! Heatwave injected at {TARGET_LAT}, {TARGET_LON} -> {OUTPUT_PATH}")

if __name__ == "__main__":
    generate_synthetic_lst_with_anomaly()
