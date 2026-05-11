import xarray as xr
import numpy as np
import pandas as pd
import os

OUTPUT_PATH = "mission_data/global_sensor_data.nc"
TARGET_LAT, TARGET_LON = 49.87, 8.65 # Darmstadt

def generate_synthetic_lst_with_anomaly():
    print("Generating Global Map with Darmstadt Heatwave...")
    
    lats = np.linspace(-90, 90, 180)
    lons = np.linspace(-180, 180, 360)
    times = pd.date_range("2024-05-11", periods=1)

    lat_mesh, lon_mesh = np.meshgrid(lats, lons, indexing='ij')
    
    # 1. Base climate (warm at equator, cold at poles)
    base_temp = 30 * np.cos(np.radians(lat_mesh))
    
    # 2. Inject the Heatwave!
    # Create a mask for pixels within 2 degrees of Darmstadt
    dist_sq = (lat_mesh - TARGET_LAT)**2 + (lon_mesh - TARGET_LON)**2
    anomaly_mask = dist_sq < 4.0 # 2-degree radius
    
    # Set those pixels to a dangerous 50 degrees Celsius
    # For everywhere else, use base temp + slight noise
    final_temp = np.where(anomaly_mask, 50.0, base_temp + np.random.normal(0, 1, base_temp.shape))

    # 3. Create Dataset
    temp_4d = final_temp[np.newaxis, :, :] 
    ds = xr.Dataset(
        data_vars=dict(lst=(["time", "lat", "lon"], temp_4d)),
        coords=dict(time=times, lat=lats, lon=lons),
    )

    ds.to_netcdf(OUTPUT_PATH)
    print(f"Success! Heatwave injected at {TARGET_LAT}, {TARGET_LON}")

if __name__ == "__main__":
    generate_synthetic_lst_with_anomaly()