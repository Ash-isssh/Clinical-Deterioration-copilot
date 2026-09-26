from src.agent import escalation


def make_risk_context(
    news2_score: int,
    response_level: str,
    monitoring: str,
    reason: str,
    single_parameter_score_3: bool = False,
    deteriorating: bool = False,
    concerning_parameters: list[str] | None = None,
):
    return {
        "news2": {
            "total": news2_score,
            "single_parameter_score_3": single_parameter_score_3,
            "response": {
                "response_level": response_level,
                "monitoring": monitoring,
                "reason": reason,
            },
        },

        "trajectory": {
            "deteriorating": deteriorating,
            "parameter_count": len(concerning_parameters or []),
            "concerning_parameters": concerning_parameters or [],
            "trends": {},
        },
    }


def fake_jev_confirms(risk_context):
    return {
        "model": "fake-jev",

        "needs_additional_escalation": {
            "probability": 0.85
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
            "probability": 0.20
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
# NEWS2 2
# ---------------------------------------------------------

def test_news2_two_uses_fast_path():

    risk_context = make_risk_context(
        news2_score=2,
        response_level="increased_monitoring",
        monitoring="minimum 4-6 hourly",
        reason="NEWS2 total is between 1 and 4",
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
# NEWS2 3 + single parameter score 3
# ---------------------------------------------------------

def test_news2_three_single_parameter_trigger():

    risk_context = make_risk_context(
        news2_score=3,
        response_level="single_parameter_trigger",
        monitoring="minimum 1 hourly",
        reason="NEWS2 score of 3 in a single parameter",
        single_parameter_score_3=True,
    )

    result = escalation.decide_escalation(
        risk_context=risk_context,
        patient_state={},
    )

    assert result["should_alert"] is True
    assert result["action"] == "single_parameter_trigger"
    assert result["jev_called"] is False
    assert result["llm_called"] is False


# ---------------------------------------------------------
# NEWS2 5
# ---------------------------------------------------------

def test_news2_five_uses_urgent_path():

    risk_context = make_risk_context(
        news2_score=5,
        response_level="urgent_response",
        monitoring="minimum 1 hourly",
        reason="NEWS2 total is 5 or more",
    )

    result = escalation.decide_escalation(
        risk_context=risk_context,
        patient_state={},
    )

    assert result["should_alert"] is True
    assert result["priority"] == "urgent"
    assert result["action"] == "urgent_response"
    assert result["jev_called"] is False
    assert result["llm_called"] is False


# ---------------------------------------------------------
# NEWS2 7 + Jev confirms
# ---------------------------------------------------------

def test_news2_seven_jev_confirms(monkeypatch):

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
        news2_score=7,
        response_level="emergency_response",
        monitoring="continuous",
        reason="NEWS2 total is 7 or more",
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
    assert result["priority"] == "emergency"
    assert result["action"] == "emergency_response"

    assert result["jev_called"] is True
    assert result["jev_confirmed"] is True
    assert result["llm_called"] is True

    assert result["source"] == "news2+jev+llm"


# ---------------------------------------------------------
# NEWS2 7 + Jev does NOT confirm
# ---------------------------------------------------------

def test_news2_seven_jev_does_not_downgrade_emergency(
    monkeypatch,
):

    monkeypatch.setattr(
        escalation,
        "ask_jev",
        fake_jev_does_not_confirm,
    )

    risk_context = make_risk_context(
        news2_score=7,
        response_level="emergency_response",
        monitoring="continuous",
        reason="NEWS2 total is 7 or more",
    )

    result = escalation.decide_escalation(
        risk_context=risk_context,
        patient_state={},
    )

    # NEWS2 emergency guardrail remains active
    assert result["should_alert"] is True
    assert result["priority"] == "emergency"
    assert result["action"] == "emergency_response"

    assert result["jev_called"] is True
    assert result["jev_confirmed"] is False

    # LLM should not be called in this branch
    assert result["llm_called"] is False

    assert result["source"] == "news2_guardrail"