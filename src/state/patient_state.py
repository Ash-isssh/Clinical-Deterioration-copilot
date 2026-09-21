"""
Evolving per-patient record: static context (age, history, meds, recent labs)
loaded once, plus incrementally updated vitals history and derived features.
"""
from dataclasses import dataclass, field


@dataclass
class PatientState:
    patient_id: str
    static_context: dict = field(default_factory=dict)   # loaded once from data/patient_profiles/
    vitals_history: list = field(default_factory=list)     # rolling window of readings
    current_score: float | None = None
    last_alert_at: float | None = None                     # for alert suppression

    def update(self, reading: dict) -> None:
        # TODO: append reading, trim to rolling window size, recompute derived features
        self.vitals_history.append(reading)
