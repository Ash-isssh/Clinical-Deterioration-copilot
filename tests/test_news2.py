"""Unit tests for NEWS2 scoring against known reference cases."""
# TODO: from src.detection.news2 import compute_news2

from src.scoring.news2 import (
    score_respiratory_rate,
    score_spo2_scale_1,
    score_systolic_bp,
    score_pulse,
    score_temperature,
    calculate_news2,
)


# def test_normal_observation():

#     result = calculate_news2(
#         respiratory_rate=16,
#         spo2=97,
#         systolic_bp=118,
#         pulse=82,
#         temperature=37.1,
#         consciousness="A",
#         on_oxygen=False,
#         new_confusion=False,
#     )

#     assert result["total"] == 0
#     assert result["single_parameter_score_3"] is False

#     response = get_news2_response(result)

#     assert response["response_level"] == "routine_monitoring"


# def test_high_respiratory_rate():

#     result = calculate_news2(
#         respiratory_rate=25,
#         spo2=97,
#         systolic_bp=118,
#         pulse=82,
#         temperature=37.1,
#         consciousness="A",
#         on_oxygen=False,
#         new_confusion=False,
#     )


#     assert result["component_scores"]["respiratory_rate"] == 3
#     assert result["total"] == 3
#     assert result["single_parameter_score_3"] is True

#     response = get_news2_response(result)

#     assert response["response_level"] == "single_parameter_trigger"

#     print(response)






#the test
import pandas as pd

from src.scoring.news2 import (
    score_respiratory_rate,
    score_spo2_scale_1,
    score_systolic_bp,
    score_pulse,
    score_temperature,
    calculate_news2,
)


def test_respiratory_rate():
    assert score_respiratory_rate(8) == 3
    assert score_respiratory_rate(10) == 1
    assert score_respiratory_rate(20) == 0
    assert score_respiratory_rate(24) == 2
    assert score_respiratory_rate(25) == 3


def test_spo2():
    assert score_spo2_scale_1(91) == 3
    assert score_spo2_scale_1(92) == 2
    assert score_spo2_scale_1(94) == 1
    assert score_spo2_scale_1(96) == 0


def test_systolic_bp():
    assert score_systolic_bp(90) == 3
    assert score_systolic_bp(95) == 2
    assert score_systolic_bp(105) == 1
    assert score_systolic_bp(120) == 0
    assert score_systolic_bp(220) == 3


def test_pulse():
    assert score_pulse(40) == 3
    assert score_pulse(45) == 1
    assert score_pulse(70) == 0
    assert score_pulse(100) == 1
    assert score_pulse(120) == 2
    assert score_pulse(131) == 3


def test_temperature():
    assert score_temperature(35.0) == 3
    assert score_temperature(35.5) == 1
    assert score_temperature(37.0) == 0
    assert score_temperature(38.5) == 1
    assert score_temperature(39.5) == 2


def test_calculate_news2():
    result = calculate_news2(
        respiratory_rate=24,
        spo2=94,
        systolic_bp=105,
        pulse=115,
        temperature=38.5,
    )

    assert result["status"] == "available_parameters_only"

    assert result["component_scores"] == {
        "respiratory_rate": 2,
        "spo2": 1,
        "systolic_bp": 1,
        "pulse": 2,
        "temperature": 1,
    }

    assert result["total"] == 7
    assert result["single_parameter_score_3"] is False


def test_calculate_news2_with_three_point_parameter():
    result = calculate_news2(
        respiratory_rate=30,
        spo2=96,
        systolic_bp=120,
        pulse=70,
        temperature=37.0,
    )

    assert result["total"] == 3
    assert result["single_parameter_score_3"] is True