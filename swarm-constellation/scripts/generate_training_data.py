import pandas as pd
import numpy as np
import os

# Define Paths relative to the script location
# We go up one level from 'scripts/' to reach the root, then into 'mission_data/'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(BASE_DIR, "mission_data", "darmstadt_training_baseline.csv")

def generate_darmstadt_data():
    print("--- Starting Synthetic Data Generation for Darmstadt ---")
    
    # We simulate 1 year of hourly readings (365 * 24 = 8760 points)
    n_points = 8760
    
    # 1. Base Temperature (Mean ~12°C for Germany)
    # 2. Add a Sine wave for Seasonal Change (Winter vs Summer)
    # 3. Add a Sine wave for Daily Change (Day vs Night)
    time = np.linspace(0, 1, n_points)
    seasonal_swing = 15 * np.sin(2 * np.pi * time) # +/- 15 degrees over a year
    daily_swing = 5 * np.sin(2 * np.pi * time * 365) # +/- 5 degrees over a day
    
    noise = np.random.normal(0, 2, n_points) # Random sensor noise
    
    temperatures = 12 + seasonal_swing + daily_swing + noise
    
    # Create DataFrame
    df = pd.DataFrame({
        'surface_temp': np.round(temperatures, 2)
    })

    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    # Save it
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Success! Baseline file generated with {len(df)} records.")
    print(f"Saved to: {OUTPUT_PATH}")

if __name__ == "__main__":
    generate_darmstadt_data()