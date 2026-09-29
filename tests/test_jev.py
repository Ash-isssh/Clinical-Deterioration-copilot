import src.agent.jev_judge as jev_judge


def test_jev_offline_judgment(monkeypatch):

    # Force offline mode so the test does not call the
    # external TypeSafe/Jev service.
    monkeypatch.setattr(
        jev_judge,
        "TYPESAFE_AVAILABLE",
        False
    )

    risk_context = {
        "news2": {
            "status": "available_parameters_only",
            "total": 3,
            "component_scores": {
                "respiratory_rate": 2,
                "spo2": 0,
                "systolic_bp": 1,
                "pulse": 0,
                "temperature": 0,
            },
            "single_parameter_score_3": False,
        },

        "trajectory": {
            "deteriorating": True,
            "parameter_count": 3,
            "concerning_parameters": [
                "respiratory_rate_increasing",
                "systolic_bp_decreasing",
                "oxygen_saturation_decreasing",
            ],
            "trends": {},
        },
    }

    result = jev_judge.ask_jev(risk_context)

    assert result["model"] == "offline-heuristic"

    assert "needs_additional_escalation" in result
    assert "trajectory_severity" in result
    assert "recommended_response" in result

    assert (
        "probability"
        in result["needs_additional_escalation"]
    )

    assert (
        "score"
        in result["trajectory_severity"]
    )

    assert (
        "choice"
        in result["recommended_response"]
    )

    # For this test case:
    # deteriorating=True and parameter_count=3
    # should trigger the strongest offline judgment.
    assert (
        result["recommended_response"]["choice"]
        == "emergency_review"
    )

    assert (
        result["trajectory_severity"]["score"]
        == 3
    )