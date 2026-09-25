"""Unit tests for NEWS2 scoring against known reference cases."""
# TODO: from src.detection.news2 import compute_news2

from src.scoring.news2 import (
    calculate_news2,
    get_news2_response,
)


def test_normal_observation():

    result = calculate_news2(
        respiratory_rate=16,
        spo2=97,
        systolic_bp=118,
        pulse=82,
        temperature=37.1,
        consciousness="A",
        on_oxygen=False,
        new_confusion=False,
    )

    assert result["total"] == 0
    assert result["single_parameter_score_3"] is False

    response = get_news2_response(result)

    assert response["response_level"] == "routine_monitoring"


def test_high_respiratory_rate():

    result = calculate_news2(
        respiratory_rate=25,
        spo2=97,
        systolic_bp=118,
        pulse=82,
        temperature=37.1,
        consciousness="A",
        on_oxygen=False,
        new_confusion=False,
    )

    
    assert result["component_scores"]["respiratory_rate"] == 3
    assert result["total"] == 3
    assert result["single_parameter_score_3"] is True

    response = get_news2_response(result)

    assert response["response_level"] == "single_parameter_trigger"

    print(response)