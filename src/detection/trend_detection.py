"""Simple, explainable rolling-window trend detection."""


def compare_rolling(values: list[float], window_size: int = 3) -> dict:
    if len(values) < 2 * window_size:
        return {"status": "insufficient_data"}

    previous_window = values[-2 * window_size : -window_size]
    current_window = values[-window_size:]
    previous_mean = sum(previous_window) / len(previous_window)
    current_mean = sum(current_window) / len(current_window)
    change = current_mean - previous_mean

    if change > 0:
        direction = "increasing"
    elif change < 0:
        direction = "decreasing"
    else:
        direction = "stable"

    return {
        "status": "ok",
        "previous_mean": round(previous_mean, 2),
        "recent_mean": round(current_mean, 2),
        "change": round(change, 2),
        "direction": direction,
    }


def detect_trends(vitals: list[dict]) -> dict:
    """Compare two short windows instead of reacting to one reading."""
    if len(vitals) < 6:
        return {"status": "insufficient_data"}

    return {
        "status": "ok",
        "heart_rate": compare_rolling([v["hr"] for v in vitals]),
        "respiratory_rate": compare_rolling([v["rr"] for v in vitals]),
        "systolic_bp": compare_rolling([v["sbp"] for v in vitals]),
        "oxygen_saturation": compare_rolling([v["o2"] for v in vitals]),
        "temperature": compare_rolling([v["temp"] for v in vitals]),
    }
