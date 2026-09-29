"""Deterministic NEWS2-derived scoring for the available demo variables.

The challenge stream provides five physiological variables in this prototype:
respiratory rate, SpO2, systolic BP, pulse and temperature. Consciousness and
oxygen-support information are not supplied, so they are not fabricated.
"""

from typing import Any


def score_respiratory_rate(rr: float) -> int:
    if rr <= 8:
        return 3
    if rr <= 11:
        return 1
    if rr <= 20:
        return 0
    if rr <= 24:
        return 2
    return 3


def score_spo2_scale_1(spo2: float) -> int:
    if spo2 <= 91:
        return 3
    if spo2 <= 93:
        return 2
    if spo2 <= 95:
        return 1
    return 0


def score_systolic_bp(sbp: float) -> int:
    if sbp <= 90:
        return 3
    if sbp <= 100:
        return 2
    if sbp <= 110:
        return 1
    if sbp <= 219:
        return 0
    return 3


def score_pulse(pulse: float) -> int:
    if pulse <= 40:
        return 3
    if pulse <= 50:
        return 1
    if pulse <= 90:
        return 0
    if pulse <= 110:
        return 1
    if pulse <= 130:
        return 2
    return 3


def score_temperature(temp: float) -> int:
    if temp <= 35.0:
        return 3
    if temp <= 36.0:
        return 1
    if temp <= 38.0:
        return 0
    if temp <= 39.0:
        return 1
    return 2


def calculate_news2(
    *, respiratory_rate: float, spo2: float, systolic_bp: float,
    pulse: float, temperature: float,
) -> dict[str, Any]:
    component_scores = {
        "respiratory_rate": score_respiratory_rate(respiratory_rate),
        "spo2": score_spo2_scale_1(spo2),
        "systolic_bp": score_systolic_bp(systolic_bp),
        "pulse": score_pulse(pulse),
        "temperature": score_temperature(temperature),
    }
    total = sum(component_scores.values())
    return {
        "status": "available_parameters_only",
        "total": total,
        "component_scores": component_scores,
        "single_parameter_score_3": any(score == 3 for score in component_scores.values()),
    }
