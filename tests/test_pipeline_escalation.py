from src.api.main import Vital
from src.pipeline.clinical_pipeline import process_vital
from src.state.state_manager import patient_states


def test_pipeline_reaches_escalation():

    # Clean patient state
    patient_states.pop(1,None)

    observations = [
    # Older window
    Vital(
        patient_id=1,
        timestamp="2026-09-26T20:00:00",
        hr=70,
        rr=14,
        sbp=130,
        dbp=80,
        o2=99,
        temp=36.5,
        alert_level="alert",
    ),
    Vital(
        patient_id=1,
        timestamp="2026-09-26T20:15:00",
        hr=70,
        rr=14,
        sbp=130,
        dbp=80,
        o2=99,
        temp=36.5,
        alert_level="alert",
    ),
    Vital(
        patient_id=1,
        timestamp="2026-09-26T20:30:00",
        hr=70,
        rr=14,
        sbp=130,
        dbp=80,
        o2=99,
        temp=36.5,
        alert_level="alert",
    ),

    # Recent window
    Vital(
        patient_id=1,
        timestamp="2026-09-26T20:45:00",
        hr=80,
        rr=16,
        sbp=120,
        dbp=80,
        o2=98,
        temp=36.8,
        alert_level="alert",
    ),
    Vital(
        patient_id=1,
        timestamp="2026-09-26T21:00:00",
        hr=90,
        rr=18,
        sbp=110,
        dbp=80,
        o2=97,
        temp=37.2,
        alert_level="alert",
    ),
    Vital(
        patient_id=1,
        timestamp="2026-09-26T21:15:00",
        hr=100,
        rr=20,
        sbp=100,
        dbp=75,
        o2=96,
        temp=37.8,
        alert_level="alert",
    ),
]

    result = None

    for observation in observations:
        result = process_vital(observation)

    assert result is not None

    # Deterministic pipeline produced its outputs
    assert "trends" in result
    assert "deterioration" in result
    assert "news2" in result
    assert "risk_context" in result
    assert "escalation" in result

    # Multiple concerning trends should be detected
    deterioration = result["deterioration"]

    print("\nTRENDS:")
    print(result["trends"])
        
    print("\nDETERIORATION:")
    print(result["deterioration"])

    assert deterioration["deteriorating"] is True, (
    f"\nTRENDS: {result['trends']}"
    f"\nDETERIORATION: {result['deterioration']}"
)
    assert deterioration["parameter_count"] >= 3

    # Risk context should preserve the actual trends
    risk_context = result["risk_context"]

    assert "news2" in risk_context
    assert "trajectory" in risk_context
    assert "trends" in risk_context["trajectory"]

    # Escalation layer should have been reached
    escalation = result["escalation"]

    assert escalation is not None
    assert "should_alert" in escalation
    assert "jev_called" in escalation
    assert "llm_called" in escalation

    # State should contain the final escalation result
    state = result["state"]

    assert state.escalation == escalation