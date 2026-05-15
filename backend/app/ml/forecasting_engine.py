import pandas as pd
import numpy as np
from typing import List, Dict

class ForecastingEngine:
    def __init__(self):
        pass

    def forecast_linear(self, history: List[Dict], periods: int = 12):
        """Simple linear regression forecast for environments without complex ML libs."""
        df = pd.DataFrame(history)
        if 'ds' not in df or 'y' not in df:
            return None, "Data must have 'ds' (date) and 'y' (value) columns"
        
        df['ds'] = pd.to_datetime(df['ds'])
        df = df.sort_values('ds')
        
        # Convert dates to ordinal for regression
        x = np.array(range(len(df))).reshape(-1, 1)
        y = df['y'].values
        
        # Simple linear fit
        slope, intercept = np.polyfit(x.flatten(), y, 1)
        
        # Forecast future points
        future_x = np.array(range(len(df), len(df) + periods)).reshape(-1, 1)
        future_y = slope * future_x.flatten() + intercept
        
        # Generate future dates
        last_date = df['ds'].max()
        future_dates = pd.date_range(start=last_date, periods=periods + 1, freq='M')[1:]
        
        results = []
        for d, v in zip(future_dates, future_y):
            results.append({"ds": d.strftime('%Y-%m-%d'), "y": float(v)})
            
        return results, None

    def detect_anomalies(self, history: List[Dict], threshold: float = 2.0):
        """Simple Z-score based anomaly detection."""
        df = pd.DataFrame(history)
        if 'y' not in df:
            return None, "Data must have 'y' column"
            
        mean = df['y'].mean()
        std = df['y'].std()
        
        df['z_score'] = (df['y'] - mean) / std
        anomalies = df[df['z_score'].abs() > threshold]
        
        return anomalies.to_dict(orient='records'), None
