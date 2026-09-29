from src.scoring.risk_ranking import build_risk_context


def test_build_risk_context():

    news2_result = {
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
    }

    deterioration_result = {
        "status": "ok",
        "deteriorating": True,
        "concerning_parameters": [
            "respiratory_rate_increasing",
            "systolic_bp_decreasing",
            "oxygen_saturation_decreasing",
        ],
        "parameter_count": 3,
        "trends": {
            "respiratory_rate": {
                "direction": "increasing"
            },
            "systolic_bp": {
                "direction": "decreasing"
            },
            "oxygen_saturation": {
                "direction": "decreasing"
            },
        },
    }

    result = build_risk_context(
        news2_result,
        deterioration_result,
        trends=deterioration_result["trends"]
    )

    assert result["news2"]["total"] == 3

    assert result["news2"]["component_scores"] == (
        news2_result["component_scores"]
    )

    assert result["trajectory"]["deteriorating"] is True

    assert result["trajectory"]["parameter_count"] == 3

    assert result["trajectory"]["concerning_parameters"] == (
        deterioration_result["concerning_parameters"]
    )