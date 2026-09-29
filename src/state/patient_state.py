"""State held for one synthetic patient during a streaming run."""

from collections import deque
from datetime import datetime
from typing import Any


class PatientState:
    def __init__(
        self,
        patient_id: int,
        age: int,
        gender: str,
        admission_diagnosis: str,
        relevant_history=None,
        current_medications=None,
        recent_labs=None,
        recent_procedures=None,
        clinical_notes=None,
        max_history: int = 20,
    ):
        self.patient_id = patient_id
        self.age = age
        self.gender = gender
        self.admission_diagnosis = admission_diagnosis

        self.relevant_history = relevant_history
        self.current_medications = current_medications or []
        self.recent_labs = recent_labs or {}
        self.recent_procedures = recent_procedures or []
        self.clinical_notes = clinical_notes

        self.vitals: deque[dict[str, Any]] = deque(maxlen=max_history)
        self.last_timestamp: datetime | None = None

        self.trends = None
        self.deterioration = None
        self.risk = None
        self.escalation = None
        self.news2 = None
        self.retrieved_evidence: list[dict] = []

        # Alert suppression / clinician loop state.
        self.last_alert_signature: tuple | None = None
        self.last_alert_timestamp: datetime | None = None
        self.suppressed_alerts = 0
        self.active_alert = False
        self.clinician_decision: dict | None = None

    def add_vital(self, vital: dict) -> None:
        """Add a reading while keeping recent history ordered by timestamp."""
        readings = list(self.vitals)
        readings.append(vital)
        readings.sort(key=lambda item: item["timestamp"])
        self.vitals.clear()
        self.vitals.extend(readings[-self.vitals.maxlen :])

        timestamps = []
        for item in self.vitals:
            value = item.get("timestamp")
            if isinstance(value, str):
                value = datetime.fromisoformat(value)
            if isinstance(value, datetime):
                timestamps.append(value)
        self.last_timestamp = max(timestamps, default=None)

    def get_recent_vitals(self) -> list[dict]:
        return list(self.vitals)

    def number_of_vitals(self) -> int:
        return len(self.vitals)

    def get_vital_series(self, vital_name: str) -> list[float]:
        return [v[vital_name] for v in self.vitals if vital_name in v]

    def update_analysis(
        self,
        trends=None,
        deterioration=None,
        news2=None,
        risk=None,
        escalation=None,
        retrieved_evidence=None,
    ) -> None:
        if trends is not None:
            self.trends = trends
        if deterioration is not None:
            self.deterioration = deterioration
        if risk is not None:
            self.risk = risk
        if escalation is not None:
            self.escalation = escalation
        if news2 is not None:
            self.news2 = news2
        if retrieved_evidence is not None:
            self.retrieved_evidence = retrieved_evidence

    def alert_signature(self, escalation: dict) -> tuple | None:
        if not escalation.get("should_alert"):
            return None

        return (
            escalation.get("priority"),
            escalation.get("action"),
            escalation.get("source"),
        )
