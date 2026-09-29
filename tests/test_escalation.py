from src.agent import escalation


def make_risk_context(
    news2_score: int = 0,
    deteriorating=None,
    concerning_parameters=None,
):
    concerning_parameters = concerning_parameters or []

    return {
        "news2": {
            "status": "available_parameters_only",
            "total": news2_score,
            "component_scores": {},
            "single_parameter_score_3": False,
        },

        "trajectory": {
            "deteriorating": deteriorating,
            "parameter_count": len(concerning_parameters),
            "concerning_parameters": concerning_parameters,
            "trends": {},
        },
    }


def fake_jev_confirms(risk_context):
    return {
        "model": "fake-jev",

        "needs_additional_escalation": {
            "probability": 0.85,
        },

        "trajectory_severity": {
            "score": 3,
            "confidence": 0.90,
            "probabilities": None,
        },

        "recommended_response": {
            "choice": "emergency_review",
            "confidence": 0.90,
            "probabilities": None,
        },

        "usage": {
            "input_tokens": 0,
            "output_tokens": 0,
        },
    }


def fake_jev_does_not_confirm(risk_context):
    return {
        "model": "fake-jev",

        "needs_additional_escalation": {
            "probability": 0.20,
        },

        "trajectory_severity": {
            "score": 0,
            "confidence": 0.90,
            "probabilities": None,
        },

        "recommended_response": {
            "choice": "routine",
            "confidence": 0.90,
            "probabilities": None,
        },

        "usage": {
            "input_tokens": 0,
            "output_tokens": 0,
        },
    }


def fake_explanation(
    risk_result,
    deterioration_result,
    patient_state,
    jev_result,
):
    return {
        "summary": "Emergency condition confirmed.",
        "recommended_action": "Immediate clinical review.",
        "retrieved_guidelines": [],
        "cited_guidelines": [],
    }


# ---------------------------------------------------------
# No deterioration
# ---------------------------------------------------------

def test_no_deterioration_uses_routine_monitoring():

    risk_context = make_risk_context(
        news2_score=0,
        deteriorating=False,
        concerning_parameters=[],
    )

    result = escalation.decide_escalation(
        risk_context=risk_context,
        patient_state={},
    )

    assert result["should_alert"] is False
    assert result["action"] == "routine_monitoring"
    assert result["jev_called"] is False
    assert result["llm_called"] is False


# ---------------------------------------------------------
# Insufficient data
# ---------------------------------------------------------

def test_insufficient_data_does_not_escalate():

    risk_context = make_risk_context(
        news2_score=0,
        deteriorating=None,
        concerning_parameters=[],
    )

    result = escalation.decide_escalation(
        risk_context=risk_context,
        patient_state={},
    )

    assert result["should_alert"] is False
    assert result["action"] == "insufficient_data"
    assert result["jev_called"] is False
    assert result["llm_called"] is False


# ---------------------------------------------------------
# 1-2 concerning parameters
# ---------------------------------------------------------

def test_limited_deterioration_uses_increased_monitoring():

    risk_context = make_risk_context(
        news2_score=1,
        deteriorating=True,
        concerning_parameters=[
            "respiratory_rate_increasing",
            "temperature_increasing",
        ],
    )

    result = escalation.decide_escalation(
        risk_context=risk_context,
        patient_state={},
    )

    assert result["should_alert"] is False
    assert result["action"] == "increased_monitoring"
    assert result["jev_called"] is False
    assert result["llm_called"] is False


# ---------------------------------------------------------
# 3+ concerning parameters + Jev confirms
# ---------------------------------------------------------

def test_strong_deterioration_jev_confirms(monkeypatch):

    monkeypatch.setattr(
        escalation,
        "ask_jev",
        fake_jev_confirms,
    )

    monkeypatch.setattr(
        escalation,
        "generate_explanation",
        fake_explanation,
    )

    risk_context = make_risk_context(
        news2_score=3,
        deteriorating=True,
        concerning_parameters=[
            "heart_rate_increasing",
            "respiratory_rate_increasing",
            "oxygen_saturation_decreasing",
        ],
    )

    result = escalation.decide_escalation(
        risk_context=risk_context,
        patient_state={},
    )

    assert result["should_alert"] is True
    assert result["priority"] == "high"
    assert result["action"] == "clinical_review"

    assert result["jev_called"] is True
    assert result["jev_confirmed"] is True
    assert result["llm_called"] is False

    assert result["source"] == "jev+rag"


# ---------------------------------------------------------
# 3+ concerning parameters + Jev does not confirm
# ---------------------------------------------------------

def test_strong_deterioration_jev_does_not_confirm(monkeypatch):

    monkeypatch.setattr(
        escalation,
        "ask_jev",
        fake_jev_does_not_confirm,
    )

    risk_context = make_risk_context(
        news2_score=3,
        deteriorating=True,
        concerning_parameters=[
            "heart_rate_increasing",
            "respiratory_rate_increasing",
            "oxygen_saturation_decreasing",
        ],
    )

    result = escalation.decide_escalation(
        risk_context=risk_context,
        patient_state={},
    )

    assert result["should_alert"] is False
    assert result["priority"] == "watch"
    assert result["action"] == "increased_monitoring"

    assert result["jev_called"] is True
    assert result["jev_confirmed"] is False
    assert result["llm_called"] is False

    assert result["source"] == "jev"