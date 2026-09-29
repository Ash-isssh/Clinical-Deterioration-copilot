"""FastAPI backend for the streaming copilot and clinician dashboard."""

from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.api.websocket import manager
from src.audit.logger import append_event, read_events
from src.pipeline.clinical_pipeline import process_vital
from src.rag.index_builder import build_index
from src.state.state_manager import get_patient_state, list_patient_states, reset_patient_states


BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_FILE = BASE_DIR / "frontend" / "index.html"

@asynccontextmanager
async def lifespan(app):
    # The JSON index is bundled, so startup is fast and deterministic.
    build_index()
    yield


app = FastAPI(title="Clinical Deterioration Copilot", version="1.0.0", lifespan=lifespan)


class Vital(BaseModel):
    patient_id: int = Field(gt=0)
    timestamp: datetime
    hr: float
    rr: float
    sbp: float
    dbp: float
    o2: float
    temp: float
    alert_level: str = "alert"


class ClinicianDecision(BaseModel):
    action: str
    note: str = ""


@app.get("/")
def root():
    return FileResponse(FRONTEND_FILE)


@app.get("/dashboard")
def dashboard():
    return FileResponse(FRONTEND_FILE)


@app.get("/health")
def health():
    return {"status": "ok", "patients_with_live_state": len(list_patient_states())}


@app.post("/vitals")
async def receive_vitals(observation: Vital):
    try:
        result = process_vital(observation)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    state = result["state"]
    payload = {
        "status": result["status"],
        "reason": result.get("reason"),
        "patient_id": observation.patient_id,
        "observations_stored": state.number_of_vitals(),
        "trends": result.get("trends"),
        "deterioration": result.get("deterioration"),
        "news2": result.get("news2"),
        "risk_context": result.get("risk_context"),
        "retrieved_evidence": result.get("retrieved_evidence"),
        "escalation": result.get("escalation"),
    }
    await manager.broadcast({"type": "vital_processed", "data": payload})
    return payload


@app.get("/patients")
def patients():
    rows = []
    rank = {"emergency": 4, "high": 3, "urgent": 3, "medium": 2, "watch": 2, "low": 1}
    for state in list_patient_states():
        escalation = state.escalation or {}
        news2_score = (state.news2 or {}).get("total", 0)
        rows.append({
            "patient_id": state.patient_id,
            "age": state.age,
            "diagnosis": state.admission_diagnosis,
            "risk_level": (state.risk or {}).get("risk_level", "UNKNOWN"),
            "news2": news2_score,
            "priority": escalation.get("priority", "low"),
            "action": escalation.get("action", "insufficient_data"),
            "should_alert": escalation.get("should_alert", False),
            "alert_suppressed": escalation.get("alert_suppressed", False),
            "observations": state.number_of_vitals(),
            "clinician_decision": state.clinician_decision,
        })
    rows.sort(key=lambda row: (-rank.get(row["priority"], 0), -row["news2"], row["patient_id"]))
    return {"patients": rows}


@app.get("/patients/{patient_id}/state")
def patient_state(patient_id: int):
    state = get_patient_state(patient_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} has no live state")

    return {
        "patient_id": state.patient_id,
        "age": state.age,
        "gender": state.gender,
        "admission_diagnosis": state.admission_diagnosis,
        "relevant_history": state.relevant_history,
        "current_medications": state.current_medications,
        "recent_labs": state.recent_labs,
        "observations_stored": state.number_of_vitals(),
        "recent_vitals": state.get_recent_vitals(),
        "trends": state.trends,
        "deterioration": state.deterioration,
        "news2": state.news2,
        "risk": state.risk,
        "retrieved_evidence": state.retrieved_evidence,
        "escalation": state.escalation,
        "suppressed_alerts": state.suppressed_alerts,
        "clinician_decision": state.clinician_decision,
    }


@app.post("/patients/{patient_id}/decision")
async def clinician_decision(patient_id: int, decision: ClinicianDecision):
    allowed = {"accept", "dismiss", "defer", "investigate"}
    action = decision.action.lower().strip()
    if action not in allowed:
        raise HTTPException(status_code=400, detail=f"action must be one of {sorted(allowed)}")

    state = get_patient_state(patient_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} has no live state")

    state.clinician_decision = {
        "action": action,
        "note": decision.note,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    if action in {"accept", "dismiss"}:
        state.active_alert = False

    event = append_event("clinician_decision", patient_id, state.clinician_decision)
    await manager.broadcast({"type": "clinician_decision", "data": event})
    return state.clinician_decision


@app.get("/audit")
def audit(patient_id: int | None = None):
    return {"events": read_events(patient_id)}


@app.post("/demo/reset")
async def reset_demo():
    reset_patient_states()
    append_event("demo_reset", None, {})
    await manager.broadcast({"type": "demo_reset", "data": {}})
    return {"status": "reset"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await websocket.send_json({"type": "connected", "data": {"message": "live feed connected"}})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
