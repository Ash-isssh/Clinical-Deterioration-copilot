"""Combine deterministic clinical evidence into a sortable risk context."""


def build_risk_context(news2_result: dict, deterioration_result: dict, trends: dict) -> dict:
    parameter_count = deterioration_result.get("parameter_count", 0)
    news2_total = news2_result.get("total", 0)

    if deterioration_result.get("deteriorating") is None:
        risk_level = "UNKNOWN"
    elif news2_total >= 7 or parameter_count >= 4:
        risk_level = "CRITICAL"
    elif news2_total >= 5 or parameter_count >= 3:
        risk_level = "HIGH"
    elif news2_total >= 1 or parameter_count >= 1:
        risk_level = "WATCH"
    else:
        risk_level = "LOW"

    return {
        "risk_level": risk_level,
        "news2": {
            "status": news2_result.get("status"),
            "total": news2_total,
            "component_scores": news2_result.get("component_scores", {}),
            "single_parameter_score_3": news2_result.get("single_parameter_score_3", False),
        },
        "trajectory": {
            "deteriorating": deterioration_result.get("deteriorating"),
            "parameter_count": parameter_count,
            "concerning_parameters": deterioration_result.get("concerning_parameters", []),
            "trends": trends,
        },
    }
