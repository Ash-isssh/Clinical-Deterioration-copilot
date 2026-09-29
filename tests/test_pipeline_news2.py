from src.api.main import Vital
from src.pipeline.clinical_pipeline import process_vital
from src.state.state_manager import patient_states


def test_news2_uses_latest_vital():

    # Start with a clean state for patient 1
    patient_states.pop(1, None)

    # First observation: clearly abnormal
    observation_1 = Vital(
        patient_id=1,
        timestamp="2026-09-26T20:00:00",
        hr=120,
        rr=25,
        sbp=85,
        dbp=50,
        o2=90,
        temp=39.5,
        alert_level="alert",
    )

    result_1 = process_vital(observation_1)

    news2_1 = result_1["news2"]

    assert news2_1["component_scores"] == {
        "respiratory_rate": 3,
        "spo2": 3,
        "systolic_bp": 3,
        "pulse": 2,
        "temperature": 2,
    }

    assert news2_1["total"] == 13


    # Second observation: completely normal
    observation_2 = Vital(
        patient_id=1,
        timestamp="2026-09-26T20:15:00",
        hr=75,
        rr=16,
        sbp=120,
        dbp=80,
        o2=98,
        temp=37.0,
        alert_level="alert",
    )

    result_2 = process_vital(observation_2)

    news2_2 = result_2["news2"]

    assert news2_2["component_scores"] == {
        "respiratory_rate": 0,
        "spo2": 0,
        "systolic_bp": 0,
        "pulse": 0,
        "temperature": 0,
    }

    assert news2_2["total"] == 0