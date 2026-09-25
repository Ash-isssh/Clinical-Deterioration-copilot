def detect_deterioration(trends):
    if trends.get("status") == "insufficient_data":
        return {
            "status": "insufficient_data",
            "deteriorating": False
        }

    concerning_changes = []

    # Directions that we consider concerning for our prototype
    if trends["heart_rate"]["direction"] == "increasing":
        concerning_changes.append("heart_rate_increasing")

    if trends["respiratory_rate"]["direction"] == "increasing":
        concerning_changes.append("respiratory_rate_increasing")

    if trends["systolic_bp"]["direction"] == "decreasing":
        concerning_changes.append("systolic_bp_decreasing")

    if trends["oxygen_saturation"]["direction"] == "decreasing":
        concerning_changes.append("oxygen_saturation_decreasing")

    if trends["temperature"]["direction"] == "increasing":
        concerning_changes.append("temperature_increasing")

    parameter_count = len(concerning_changes)

    # heuristic
    deteriorating = parameter_count >= 3

    return {
        "status": "ok",
        "deteriorating": deteriorating,
        "concerning_parameters": concerning_changes,
        "parameter_count": parameter_count
    }