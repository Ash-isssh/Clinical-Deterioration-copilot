"""
FastAPI app entrypoint — REST endpoints for cohort state + the WebSocket
endpoint for the live dashboard.
"""
from fastapi import FastAPI
from datetime import datetime
from pydantic import BaseModel

from src.state.state_manager import get_patient_state
from src.pipeline.clinical_pipeline import process_vital

app = FastAPI(title="Clinical Deterioration Copilot")

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

    state, trends, deterioration_result = process_vital(observation)

    print(
        f"Patient {observation.patient_id}: "
        f"{state.number_of_vitals()} observations stored"
    )

    return {
        "status": "received",
        "patient_id": observation.patient_id,
        "observations_stored": state.number_of_vitals(),
        "trends": trends,
        "deterioration": deterioration_result
    }  

@app.get("/patients/{patient_id}/state")
def get_patient_state_endpoint(patient_id: int):

    state = get_patient_state(patient_id)

    if state is None:
        return {
            "status": "error",
            "message": f"Patient {patient_id} not found"
        }

    return {
        "patient_id": state.patient_id,
        "age": state.age,
        "gender": state.gender,
        "admission_diagnosis": state.admission_diagnosis,
        "observations_stored": state.number_of_vitals(),
        "recent_vitals": state.get_recent_vitals(),
        "trends": state.trends,
        "deterioration": state.deterioration,
        "risk": state.risk,
        "escalation": state.escalation,
    }