"""
Deterministic NEWS2 calculation.

This module calculates NEWS2 from individual physiological
measurements. It does not use an LLM or Jev.

Source:
Royal College of Physicians NEWS2 scoring charts.
"""
from typing import Any


def score_respiratory_rate(rr: float) -> int:
    if rr <= 8:
        return 3
    elif rr <= 11:
        return 1
    elif rr <= 20:
        return 0
    elif rr <= 24:
        return 2
    else:
        return 3


def score_spo2_scale_1(spo2: float) -> int:
    if spo2 <= 91:
        return 3
    elif spo2 <= 93:
        return 2
    elif spo2 <= 95:
        return 1
    else:
        return 0


def score_systolic_bp(sbp: float) -> int:
    if sbp <= 90:
        return 3
    elif sbp <= 100:
        return 2
    elif sbp <= 110:
        return 1
    elif sbp <= 219:
        return 0
    else:
        return 3


def score_pulse(pulse: float) -> int:
    if pulse <= 40:
        return 3
    elif pulse <= 50:
        return 1
    elif pulse <= 90:
        return 0
    elif pulse <= 110:
        return 1
    elif pulse <= 130:
        return 2
    else:
        return 3


def score_temperature(temp: float) -> int:
    if temp <= 35.0:
        return 3
    elif temp <= 36.0:
        return 1
    elif temp <= 38.0:
        return 0
    elif temp <= 39.0:
        return 1
    else:
        return 2


def score_consciousness(
    consciousness: str,
    new_confusion: bool = False,
) -> int:
    """
    NEWS2 gives 3 points for new confusion or V/P/U.

    Chronic confusion should not receive the new-confusion score.
    """

    consciousness = consciousness.upper()

    if new_confusion:
        return 3

    if consciousness in {"V", "P", "U"}:
        return 3

    if consciousness == "C":
        return 3

    if consciousness == "A":
        return 0

    raise ValueError(
        "consciousness must be one of A, C, V, P, U"
    )


def score_oxygen_support(on_oxygen: bool) -> int:
    """
    NEWS2 oxygen-support component.

    Air = 0
    Supplemental oxygen = 2
    """

    return 2 if on_oxygen else 0


def calculate_news2(
    *,
    respiratory_rate: float,
    spo2: float,
    systolic_bp: float,
    pulse: float,
    temperature: float,
    consciousness: str,
    on_oxygen: bool,
    new_confusion: bool = False,
) -> dict[str, Any]:

    component_scores = {
        "respiratory_rate": score_respiratory_rate(
            respiratory_rate
        ),

        "spo2": score_spo2_scale_1(spo2),

        "systolic_bp": score_systolic_bp(
            systolic_bp
        ),

        "pulse": score_pulse(
            pulse
        ),

        "consciousness": score_consciousness(
            consciousness,
            new_confusion=new_confusion,
        ),

        "temperature": score_temperature(
            temperature
        ),

        "oxygen_support": score_oxygen_support(
            on_oxygen
        ),
    }

    total = sum(component_scores.values())

    single_parameter_score_3 = any(
        score == 3
        for score in component_scores.values()
    )

    news2_result = {
        "total": total,
        "component_scores": component_scores,
        "single_parameter_score_3": single_parameter_score_3,
    }
    # Calculate the response from that result
    news2_result["response"] = get_news2_response(news2_result)

    return news2_result


def get_news2_response(news2_result: dict) -> dict:
    """
    Convert the NEWS2 score into the response threshold.

    This is deterministic and should remain outside Jev.
    """

    total = news2_result["total"]
    single_parameter_score_3 = news2_result[
        "single_parameter_score_3"
    ]

    if total >= 7:
        return {
            "response_level": "emergency_response",
            "monitoring": "continuous",
            "reason": "NEWS2 total is 7 or more",
        }

    if total >= 5:
        return {
            "response_level": "urgent_response",
            "monitoring": "minimum 1 hourly",
            "reason": "NEWS2 total is 5 or more",
        }

    if single_parameter_score_3:
        return {
            "response_level": "single_parameter_trigger",
            "monitoring": "minimum 1 hourly",
            "reason": "NEWS2 score of 3 in a single parameter",
        }

    if total >= 1:
        return {
            "response_level": "increased_monitoring",
            "monitoring": "minimum 4-6 hourly",
            "reason": "NEWS2 total is between 1 and 4",
        }

    return {
        "response_level": "routine_monitoring",
        "monitoring": "minimum 12 hourly",
        "reason": "NEWS2 total is 0",
    }