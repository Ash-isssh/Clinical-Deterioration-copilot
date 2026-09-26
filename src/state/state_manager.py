import pandas as pd
from datetime import datetime
from src.state.patient_state import PatientState


DEMOGRAPHICS_FILE = "data/patient_profiles/patient_demographics.csv"
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


patient_states:dict[int, PatientState]={}

def get_or_create_patient_state(patient_id: int) -> PatientState:
    if patient_id not in patient_states:

        profile = patient_profiles.get(patient_id)

        if profile is None:
            raise ValueError(f"Patient {patient_id} not found")

        patient_states[patient_id] = PatientState(
            patient_id=patient_id,
            age=profile["age"],
            gender=profile["gender"],
            admission_diagnosis=profile["admission_diagnosis"],
        )

    return patient_states[patient_id]


def get_patient_state(patient_id: int):
    return patient_states.get(patient_id)