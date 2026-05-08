import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib
import os

class SaliencyEngine:
    def __init__(self, baseline_path):
        self.baseline_path = baseline_path
        self.model = IsolationForest(contamination=0.01, random_state=42)
        self.is_trained = False

    def train_model(self):
        """Trains the model on historical baseline data."""
        if not os.path.exists(self.baseline_path):
            print(f"[AI] Error: Baseline file {self.baseline_path} not found.")
            return
        
        print("[AI] Training Saliency Model on Darmstadt baseline...")
        data = pd.read_csv(self.baseline_path)
        
        # Isolation Forest expects a 2D array: [[val1], [val2], ...]
        X = data[['surface_temp']].values
        self.model.fit(X)
        self.is_trained = True
        print("[AI] Training Complete. Contamination threshold set to 1%.")

    def analyze_reading(self, temp_value):
        """
        Predicts if a temperature reading is an anomaly.
        Returns: True if Anomaly (-1), False if Normal (1)
        """
        if not self.is_trained:
            return False # Default to normal if not trained
        
        # Reshape for inference
        prediction = self.model.predict([[temp_value]])[0]
        
        # Isolation Forest returns -1 for anomalies and 1 for normal
        return True if prediction == -1 else False