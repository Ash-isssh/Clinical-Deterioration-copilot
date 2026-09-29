"""Convert multi-parameter directions into a small, explainable signal."""


CONCERNING_DIRECTIONS = {
    "heart_rate": "increasing",
    "respiratory_rate": "increasing",
    "systolic_bp": "decreasing",
    "oxygen_saturation": "decreasing",
    "temperature": "increasing",
}

PARAMETER_LABELS = {
    "heart_rate": "heart_rate_increasing",
    "respiratory_rate": "respiratory_rate_increasing",
    "systolic_bp": "systolic_bp_decreasing",
    "oxygen_saturation": "oxygen_saturation_decreasing",
    "temperature": "temperature_increasing",
}


def detect_deterioration(trends: dict) -> dict:
    if trends.get("status") == "insufficient_data":
        return {
            "status": "insufficient_data",
            "deteriorating": None,
            "concerning_parameters": [],
            "parameter_count": 0,
        }

    concerning_changes = []
    for parameter, expected_direction in CONCERNING_DIRECTIONS.items():
        if trends.get(parameter, {}).get("direction") == expected_direction:
            concerning_changes.append(PARAMETER_LABELS[parameter])

    parameter_count = len(concerning_changes)
    return {
        "status": "ok",
        "deteriorating": parameter_count >= 3,
        "concerning_parameters": concerning_changes,
        "parameter_count": parameter_count,
    }
