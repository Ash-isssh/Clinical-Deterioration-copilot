from datetime import datetime, timedelta

import pytest

from src.api.main import Vital
from src.pipeline.clinical_pipeline import process_vital
from src.state.state_manager import patient_states


def make_vital(patient_id=1, offset=0, hr=75, rr=16, sbp=120, o2=98, temp=37.0):
    return Vital(
        patient_id=patient_id,
        timestamp=datetime(2026, 9, 29, 10, 0) + timedelta(minutes=offset),
        hr=hr,
        rr=rr,
        sbp=sbp,
        dbp=80,
        o2=o2,
        temp=temp,
        alert_level="alert",
    )


def test_duplicate_timestamp_is_ignored():
    patient_states.pop(1, None)
    first = make_vital(offset=0)
    process_vital(first)
    result = process_vital(first)
    assert result["status"] == "ignored"
    assert result["reason"] == "duplicate_timestamp"
    assert result["state"].number_of_vitals() == 1


def test_out_of_order_reading_is_kept_in_timestamp_order():
    patient_states.pop(1, None)
    process_vital(make_vital(offset=10))
    result = process_vital(make_vital(offset=5, hr=90))
    assert result["status"] == "processed"
    assert result["out_of_order"] is True
    timestamps = [v["timestamp"] for v in result["state"].get_recent_vitals()]
    assert timestamps == sorted(timestamps)


def test_impossible_reading_is_rejected():
    patient_states.pop(1, None)
    with pytest.raises(ValueError):
        process_vital(make_vital(hr=500))


def test_repeated_same_priority_alert_is_suppressed():
    patient_states.pop(3, None)
    results = []
    for offset, hr, rr, sbp, o2, temp in [
        (0, 75, 16, 120, 98, 37.0),
        (15, 85, 18, 115, 97, 37.3),
        (30, 95, 21, 105, 94, 37.8),
        (45, 105, 23, 95, 92, 38.2),
        (60, 110, 24, 90, 91, 38.5),
        (75, 115, 25, 88, 90, 38.7),
        (90, 118, 26, 86, 89, 39.0),
    ]:
        results.append(process_vital(make_vital(3, offset, hr, rr, sbp, o2, temp)))

    assert any(r["escalation"].get("should_alert") for r in results)
    assert any(r["escalation"].get("alert_suppressed") for r in results)
