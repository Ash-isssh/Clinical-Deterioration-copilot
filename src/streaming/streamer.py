"""Replay one synthetic patient as a live HTTP stream."""

import argparse
import os
import time

import pandas as pd
import requests


DATA_FILE = os.getenv("DATA_FILE", "data/raw/synthetic_vitals.csv")
API_URL = os.getenv("API_URL", "http://127.0.0.1:8001/vitals")


def send_vitals(patient_id: int = 3, delay: float = 0.35, max_rows: int = 45, start_row: int = 0):
    df = pd.read_csv(DATA_FILE)
    patient_data = df[df["patient_id"] == patient_id].iloc[start_row : start_row + max_rows]
    if patient_data.empty:
        raise ValueError(f"No rows found for patient {patient_id}")

    session = requests.Session()
    print(f"Streaming patient {patient_id}: {len(patient_data)} observations -> {API_URL}")
    for _, row in patient_data.iterrows():
        payload = {
            "patient_id": int(row["patient_id"]),
            "timestamp": row["timestamp"],
            "hr": float(row["heart_rate"]),
            "rr": float(row["resp_rate"]),
            "sbp": float(row["sbp"]),
            "dbp": float(row["dbp"]),
            "o2": float(row["o2_sat"]),
            "temp": float(row["temperature"]),
            "alert_level": str(row["alert_level"]),
        }
        response = session.post(API_URL, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()
        escalation = result.get("escalation") or {}
        print(
            f"P{patient_id} | stored={result.get('observations_stored', 0):>2} "
            f"| NEWS2={result.get('news2', {}).get('total', '-') :>2} "
            f"| trend={result.get('deterioration', {}).get('parameter_count', 0)} "
            f"| action={escalation.get('action', '-')} "
            f"| alert={escalation.get('should_alert', False)}"
            f"{' (suppressed)' if escalation.get('alert_suppressed') else ''}"
        )
        time.sleep(delay)


def main():
    parser = argparse.ArgumentParser(description="Replay synthetic vitals through the FastAPI endpoint")
    parser.add_argument("--patient", type=int, default=int(os.getenv("DEMO_PATIENT_ID", "3")))
    parser.add_argument("--delay", type=float, default=float(os.getenv("DEMO_DELAY", "0.35")))
    parser.add_argument("--rows", type=int, default=int(os.getenv("DEMO_ROWS", "45")))
    parser.add_argument("--start", type=int, default=int(os.getenv("DEMO_START_ROW", "80")))
    args = parser.parse_args()
    send_vitals(args.patient, args.delay, args.rows, args.start)


if __name__ == "__main__":
    main()
