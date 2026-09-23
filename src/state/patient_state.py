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

    def add_vital(self, vital: dict):
        self.vitals.append(vital)

    def get_recent_vitals(self):
        return list(self.vitals)

    def number_of_vitals(self):
        return len(self.vitals)