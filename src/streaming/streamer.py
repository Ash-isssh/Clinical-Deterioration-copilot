import pandas as pd
import requests
import time

API_URL="http://127.0.0.1:8001/vitals"
DATA_FILE="data/raw/synthetic_vitals.csv"

def send_vitals():
    df = pd.read_csv(DATA_FILE)
    patient_data = df[df["patient_id"] == 1]
    for _, row in patient_data.iterrows():
        payload = {
            "patient_id": int(row['patient_id']),
            "timestamp": row['timestamp'],
            "hr": float(row['heart_rate']),
            "rr": float(row['resp_rate']),
            "sbp": float(row['sbp']),
            "dbp": float(row['dbp']),
            "o2": float(row['o2_sat']),
            "temp": float(row['temperature']),
            "alert_level": row['alert_level']
        }
        response = requests.post(API_URL, json=payload)
        print(f"Sent vitals for patient {row['patient_id']}, response: {response.status_code}")
        time.sleep(1)  # Simulate a delay between readings
if __name__ == "__main__":
    send_vitals()