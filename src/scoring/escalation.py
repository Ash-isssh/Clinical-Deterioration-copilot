"""
Escalation orchestration.

NEWS2 2  → no Jev
NEWS2 5  → urgent, no Jev
NEWS2 7 + Jev confirms → LLM path
NEWS2 7 + Jev rejects → emergency still preserved

Pipeline:

    risk_context
        |
        +---- NEWS2 < 7 ----> deterministic fast path
        |
        +---- NEWS2 >= 7 ---> Jev
                                  |
                           +------+------+
                           |             |
                        confirms     not confirmed
                           |             |
                           v             v
                       LLM + RAG    NEWS2 emergency
                                    guardrail remains
"""

from src.agent.jev_judge import ask_jev
from src.agent.llm_explain import generate_explanation


NEWS2_URGENT_THRESHOLD = 5
NEWS2_EMERGENCY_THRESHOLD = 7


def decide_escalation(
    risk_context: dict,
    patient_state: dict,
) -> dict:
    """
    Main escalation decision.

    Jev and the LLM are only used for NEWS2 >= 7.

    NEWS2 7+ remains an emergency-response guardrail even when
    Jev does not provide additional confirmation.
    """

    news2 = risk_context["news2"]
    trajectory = risk_context["trajectory"]

    score = news2["total"]
    response = news2["response"]

    # =========================================================
    # PATH 1
    # NEWS2 0-4
    # =========================================================

    if score < NEWS2_URGENT_THRESHOLD:

        # Special single-parameter score of 3
        if (
            score == 3
            and news2.get("single_parameter_score_3", False)
        ):
            return {
                "should_alert": True,
                "priority": "medium",
                "action": "single_parameter_trigger",
                "reason": response["reason"],
                "monitoring": response["monitoring"],
                "source": "news2",
                "news2_score": score,
                "jev_called": False,
                "llm_called": False,
                "trajectory": trajectory,
            }

        # NEWS2 1-4
        if score >= 1:
            return {
                "should_alert": False,
                "priority": "low",
                "action": "increased_monitoring",
                "reason": response["reason"],
                "monitoring": response["monitoring"],
                "source": "news2",
                "news2_score": score,
                "jev_called": False,
                "llm_called": False,
                "trajectory": trajectory,
            }

        # NEWS2 = 0
        return {
            "should_alert": False,
            "priority": "low",
            "action": "routine_monitoring",
            "reason": response["reason"],
            "monitoring": response["monitoring"],
            "source": "news2",
            "news2_score": score,
            "jev_called": False,
            "llm_called": False,
            "trajectory": trajectory,
        }

    # =========================================================
    # PATH 2
    # NEWS2 5-6
    # =========================================================

    if score < NEWS2_EMERGENCY_THRESHOLD:

        return {
            "should_alert": True,
            "priority": "urgent",
            "action": "urgent_response",
            "reason": response["reason"],
            "monitoring": response["monitoring"],
            "source": "news2",
            "news2_score": score,
            "jev_called": False,
            "llm_called": False,
            "trajectory": trajectory,
        }

    # =========================================================
    # PATH 3
    # NEWS2 >= 7
    # =========================================================

    jev_result = ask_jev(risk_context)

    probability = jev_result[
        "needs_additional_escalation"
    ]["probability"]

    recommended_response = jev_result[
        "recommended_response"
    ]["choice"]

    # Our Jev confirmation rule
    jev_confirms = (
        probability >= 0.60
        or recommended_response == "emergency_review"
    )

    # =========================================================
    # JEV CONFIRMS
    # =========================================================

    if jev_confirms:

        # LLM + RAG only after Jev confirmation.
        explanation = generate_explanation(
            risk_result={
                "risk_score": score,
                "risk_level": "emergency",
            },
            deterioration_result=trajectory,
            patient_state=patient_state,
            jev_result=jev_result,
        )

        return {
            "should_alert": True,
            "priority": "emergency",
            "action": "emergency_response",

            "reason": explanation["summary"],
            "monitoring": "continuous",

            "source": "news2+jev+llm",

            "news2_score": score,

            "jev_called": True,
            "jev_confirmed": True,

            "llm_called": True,

            "jev_detail": jev_result,

            "explanation": explanation,

            "trajectory": trajectory,
        }

    # =========================================================
    # JEV DOES NOT CONFIRM
    # =========================================================

    # IMPORTANT:
    # NEWS2 >= 7 is still an emergency threshold.
    # Jev disagreement does NOT downgrade it.

    return {
        "should_alert": True,
        "priority": "emergency",
        "action": "emergency_response",

        "reason": (
            f"NEWS2={score} meets the emergency-response "
            "threshold, although Jev did not confirm "
            "additional trajectory concern."
        ),

        "monitoring": "continuous",

        "source": "news2_guardrail",

        "news2_score": score,

        "jev_called": True,
        "jev_confirmed": False,

        "llm_called": False,

        "jev_detail": jev_result,

        "trajectory": trajectory,
    }