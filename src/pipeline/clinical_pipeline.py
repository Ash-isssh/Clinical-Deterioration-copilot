"""End-to-end processing of one streamed observation."""

from datetime import datetime, timedelta

from src.audit.logger import append_event
from src.detection.deterioration_detecter import detect_deterioration
from src.detection.trend_detection import detect_trends
from src.agent.escalation import decide_escalation
from src.rag.retriever import retrieve_for_patient
from src.scoring.news2 import calculate_news2
from src.scoring.risk_ranking import build_risk_context
from src.state.state_manager import get_or_create_patient_state



def _validate_observation(observation) -> None:
    limits = {
        "hr": (20, 250),
        "rr": (4, 60),
        "sbp": (40, 250),
        "dbp": (20, 180),
        "o2": (50, 100),
        "temp": (30, 45),
    }
    for name, (low, high) in limits.items():
        value = getattr(observation, name)
        if not low <= value <= high:
            raise ValueError(f"{name}={value} is outside demo validation range {low}-{high}")


def _suppress_repeat_alert(state, escalation, timestamp: datetime) -> dict:
    if not escalation.get("should_alert"):
        return escalation

    signature = state.alert_signature(escalation)
    if signature is None:
        return escalation

    if state.last_alert_signature == signature and state.last_alert_timestamp is not None:
        elapsed = timestamp - state.last_alert_timestamp
        if timedelta(minutes=30) > elapsed >= timedelta(0):
            state.suppressed_alerts += 1
            return {
                **escalation,
                "should_alert": False,
                "alert_suppressed": True,
                "suppressed_count": state.suppressed_alerts,
                "suppression_reason": "same alert signature within 30 minutes",
            }

    state.last_alert_signature = signature
    state.last_alert_timestamp = timestamp
    state.active_alert = True
    return {**escalation, "alert_suppressed": False, "suppressed_count": state.suppressed_alerts}


def process_vital(observation):
    _validate_observation(observation)
    patient_id = observation.patient_id
    state = get_or_create_patient_state(patient_id)
    vital_data = observation.model_dump()
    timestamp = observation.timestamp

    if any(existing.get("timestamp") == timestamp for existing in state.get_recent_vitals()):
        reason = "duplicate_timestamp"
        append_event("stream_rejected", patient_id, {"reason": reason, "observation": vital_data})
        return {
            "status": "ignored",
            "reason": reason,
            "state": state,
            "trends": state.trends,
            "deterioration": state.deterioration,
            "news2": state.news2,
            "risk_context": state.risk or {},
            "escalation": state.escalation,
        }

    out_of_order = state.last_timestamp is not None and timestamp < state.last_timestamp
    state.add_vital(vital_data)
    recent_vitals = state.get_recent_vitals()

    trends = detect_trends(recent_vitals)
    deterioration = detect_deterioration(trends)
    news2 = calculate_news2(
        respiratory_rate=vital_data["rr"],
        spo2=vital_data["o2"],
        systolic_bp=vital_data["sbp"],
        pulse=vital_data["hr"],
        temperature=vital_data["temp"],
    )
    risk_context = build_risk_context(news2, deterioration, trends)

    # Retrieval is done only when the state is meaningful enough to inspect.
    # Set the latest derived values before building the query.
    state.deterioration = deterioration
    state.news2 = news2
    potential_event = deterioration.get("parameter_count", 0) >= 2 or news2.get("total", 0) >= 5
    evidence_bundle = (
        retrieve_for_patient(state, k=3)
        if state.number_of_vitals() >= 6 and potential_event
        else {"query": "", "evidence": []}
    )
    state.retrieved_evidence = evidence_bundle["evidence"]

    escalation = decide_escalation(
        risk_context=risk_context,
        patient_state={
            "static_context": {
                "patient_id": state.patient_id,
                "age": state.age,
                "gender": state.gender,
                "admission_diagnosis": state.admission_diagnosis,
                "relevant_history": state.relevant_history,
                "current_medications": state.current_medications,
                "recent_labs": state.recent_labs,
            },
            "latest_vitals": vital_data,
        },
    )
    escalation = _suppress_repeat_alert(state, escalation, timestamp)

    state.update_analysis(
        trends=trends,
        deterioration=deterioration,
        news2=news2,
        risk=risk_context,
        escalation=escalation,
        retrieved_evidence=evidence_bundle["evidence"],
    )

    append_event("observation_processed", patient_id, {
        "observation": vital_data,
        "news2": news2,
        "deterioration": deterioration,
        "risk_context": risk_context,
        "escalation": escalation,
        "retrieved_evidence": evidence_bundle["evidence"],
    })

    if escalation.get("should_alert"):
        append_event("alert_created", patient_id, {
            "priority": escalation.get("priority"),
            "action": escalation.get("action"),
            "reason": escalation.get("reason", ""),
            "explanation": escalation.get("explanation"),
        })

    return {
        "status": "processed",
        "out_of_order": out_of_order,
        "state": state,
        "trends": trends,
        "deterioration": deterioration,
        "news2": news2,
        "risk_context": risk_context,
        "retrieved_evidence": evidence_bundle,
        "escalation": escalation,
    }
