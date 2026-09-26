'''It should not recalculate NEWS2.
It should not invent a new clinical score.
It should not call the LLM yet.
Its job is to package the evidence cleanly for Jev'''


from src.scoring.news2 import get_news2_response


def build_risk_context(news2_result: dict,
                        deterioration_result: dict,) -> dict:
    """
    Combine NEWS2 information with the deterioration
    detector output.

    This function does not make the final clinical decision.
    It prepares structured information for Jev.
    """

    # Get the NEWS2 response directly from our existing function
    news2_response = get_news2_response(news2_result)

    trajectory = {
        "deteriorating": deterioration_result.get(
            "deteriorating",
            False
        ),
        "parameter_count": deterioration_result.get(
            "parameter_count",
            0
        ),
        "concerning_parameters": deterioration_result.get(
            "concerning_parameters",
            []
        ),
        "trends": deterioration_result.get(
            "trends",
            {}
        ),
    }

    return {
        "news2": {
            "total": news2_result["total"],
            "component_scores": news2_result[
                "component_scores"
            ],
            "single_parameter_score_3": news2_result[
                "single_parameter_score_3"
            ],
            "response": news2_response,
        },

        "trajectory": trajectory,
    }


