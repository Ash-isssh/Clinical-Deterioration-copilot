"""Load static patient context and keep the live in-memory patient states."""

import json
from pathlib import Path

import pandas as pd

from src.state.patient_state import PatientState


BASE_DIR = Path(__file__).resolve().parents[2]
DEMOGRAPHICS_FILE = BASE_DIR / "data" / "patient_profiles" / "patient_demographics.csv"

patient_profiles: dict[int, dict] = {}
patient_states: dict[int, PatientState] = {}


def _load_jsonish(value, default):
    if pd.isna(value) or value == "":
        return default
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default


def load_demographics() -> dict[int, dict]:
    """Load the static profile once at application startup."""
    patient_profiles.clear()
    df = pd.read_csv(DEMOGRAPHICS_FILE)

    for _, row in df.iterrows():
        patient_id = int(row["patient_id"])
        patient_profiles[patient_id] = {
            "age": int(row["age"]),
            "gender": str(row["gender"]),
            "admission_diagnosis": str(row["admission_diagnosis"]),
            "relevant_history": str(row["relevant_history"]),
            "current_medications": _load_jsonish(row["current_medications"], []),
            "recent_labs": _load_jsonish(row["recent_labs"], {}),
            "recent_procedures": _load_jsonish(row["recent_procedures"], []),
            "clinical_notes": str(row["clinical_notes"]),
        }

    return patient_profiles


load_demographics()


def get_or_create_patient_state(patient_id: int) -> PatientState:
    if patient_id in patient_states:
        return patient_states[patient_id]

    profile = patient_profiles.get(patient_id)
    if profile is None:
        raise ValueError(f"Patient {patient_id} not found")

    patient_states[patient_id] = PatientState(patient_id=patient_id, **profile)
    return patient_states[patient_id]


def get_patient_state(patient_id: int) -> PatientState | None:
    return patient_states.get(patient_id)


def list_patient_states() -> list[PatientState]:
    return list(patient_states.values())


def reset_patient_states() -> None:
    patient_states.clear()
