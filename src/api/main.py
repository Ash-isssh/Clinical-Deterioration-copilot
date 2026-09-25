"""
FastAPI app entrypoint — REST endpoints for cohort state + the WebSocket
endpoint for the live dashboard.
"""

from fastapi import FastAPI
from datetime import datetime
from pydantic import BaseModel
from src.state.patient_state import PatientState
import pandas as pd
from src.detection.trend_detection import detect_trends
from src.detection.deterioration_detecter import detect_deterioration

app = FastAPI(title="Clinical Deterioration Copilot")
DEMOGRAPHICS_FILE = "data/patient_profiles/patient_demographics.csv"

patient_states:dict[int, PatientState]={}
patient_profiles: dict[int, dict] = {}
def load_demographics():
    df=pd.read_csv(DEMOGRAPHICS_FILE)
    for _, row in df.iterrows():
        patient_id=row['patient_id']
        patient_profiles[patient_id] = {
            "age": int(row["age"]),
            "gender": row["gender"],
            "admission_diagnosis": row["admission_diagnosis"],
        }
load_demographics()
#patient_id -> PatientState
class Vital(BaseModel):
    patient_id: int
    timestamp: datetime
    hr: float
    rr: float
    sbp: float
    dbp: float
    o2: float
    temp: float
    alert_level: str

#receiver is working now 
@app.get("/")
def root():
    return {"message": "Clinical Deterioration Copilot API is running"}

@app.post("/vitals")
def receive_vitals(observation: Vital):
    patient_id = observation.patient_id
    if observation.patient_id not in patient_states:
        profile=patient_profiles.get(observation.patient_id)
        patient_states[patient_id] = PatientState(
            patient_id=patient_id,
            age=profile["age"],
            gender=profile["gender"],
            admission_diagnosis=profile["admission_diagnosis"],
        )
    state = patient_states[patient_id]
    vital_data = observation.model_dump()
    state.add_vital(vital_data)
    recent_vitals = state.get_recent_vitals()
    trends = detect_trends(recent_vitals)
    deterioration_result = detect_deterioration(trends)

    print("Trends:", trends)
    print("Deterioration Result:", deterioration_result)

    print(
        f"Patient {observation.patient_id}: "
        f"{state.number_of_vitals()} observations stored"
    )

    return {
        "status": "received",
        "patient_id": patient_id,
        "observations_stored": state.number_of_vitals(),
        "trends": trends,
        "deterioration": deterioration_result
    }

@app.get("/patients/{patient_id}/state")
def get_patient_state(patient_id: int):

    if patient_id not in patient_states:
        return {
            "status": "error",
            "message": f"Patient {patient_id} not found"
        }

    state = patient_states[patient_id]

    return {
        "patient_id": state.patient_id,
        "age": state.age,
        "gender": state.gender,
        "admission_diagnosis": state.admission_diagnosis,
        "observations": state.get_recent_vitals()
    }