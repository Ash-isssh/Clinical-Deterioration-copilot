"""
Evolving per-patient record: static context (age, history, meds, recent labs)
loaded once, plus incrementally updated vitals history and derived features.
"""
from collections import deque
#using deque for efficient append and pop operations on the vitals history

class PatientState:
    def __init__(self,patient_id: int,age: int,gender: str,admission_diagnosis: str,max_history: int = 20):
        self.patient_id = patient_id
        self.age = age
        self.gender = gender
        self.admission_diagnosis = admission_diagnosis

        # Store only the most recent observations
        self.vitals = deque(maxlen=max_history)

        self.trends=None
        self.deterioration=None
        self.risk=None
        self.escalation=None

    def add_vital(self, vital: dict):
        self.vitals.append(vital)

    def get_recent_vitals(self):
        return list(self.vitals)

    def number_of_vitals(self):
        return len(self.vitals)

    def get_vital_series(self, vital_name: str):
        return [vital[vital_name] for vital in self.vitals if vital_name in vital]

    def update_analysis(
    self,
    trends=None,
    deterioration=None,
    risk=None,
    escalation=None,
):
        if trends is not None:
            self.trends = trends

        if deterioration is not None:
            self.deterioration = deterioration

        if risk is not None:
            self.risk = risk

        if escalation is not None:
            self.escalation = escalation