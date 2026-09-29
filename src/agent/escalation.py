"""Controlled escalation policy: deterministic guardrails first, optional agent second."""

from src.agent.jev_judge import ask_jev
from src.agent.llm_explain import generate_explanation

NEWS2_URGENT_THRESHOLD = 5
NEWS2_EMERGENCY_THRESHOLD = 7


def _base_response(news2, trajectory, **extra):
    response = {
        "should_alert": False,
        "priority": "low",
        "action": "routine_monitoring",
        "source": "deterministic",
        "jev_called": False,
        "jev_confirmed": False,
        "llm_called": False,
        "news2_score": news2.get("total"),
        "trajectory": trajectory,
    }
    response.update(extra)
    return response


def decide_escalation(risk_context: dict, patient_state: dict) -> dict:
    news2 = risk_context["news2"]
    trajectory = risk_context["trajectory"]
    score = news2.get("total", 0)
    deteriorating = trajectory.get("deteriorating")
    count = trajectory.get("parameter_count", 0)

    if deteriorating is None:
        return _base_response(news2, trajectory, action="insufficient_data")

    # Deterministic NEWS2 emergency guardrail is never downgraded by the agent.
    if score >= NEWS2_EMERGENCY_THRESHOLD:
        jev_result = ask_jev(risk_context)
        explanation = generate_explanation(
            risk_result={"physiological_score": score, "risk_score": score},
            deterioration_result=trajectory,
            patient_state=patient_state,
            jev_result=jev_result,
        )
        return _base_response(
            news2,
            trajectory,
            should_alert=True,
            priority="emergency",
            action="emergency_response",
            reason=explanation["summary"],
            source="news2+jev+rag",
            jev_called=True,
            jev_confirmed=jev_result["recommended_response"]["choice"] == "emergency_review",
            llm_called=explanation.get("mode") == "anthropic",
            jev_detail=jev_result,
            explanation=explanation,
        )

    if score >= NEWS2_URGENT_THRESHOLD:
        return _base_response(
            news2,
            trajectory,
            should_alert=True,
            priority="urgent",
            action="urgent_response",
            reason=f"NEWS2-derived score is {score}; urgent clinical review is appropriate.",
            source="news2",
        )

    if not deteriorating:
        return _base_response(news2, trajectory, action="routine_monitoring")

    if count < 3:
        return _base_response(
            news2,
            trajectory,
            priority="watch",
            action="increased_monitoring",
            reason=f"{count} concerning parameter trends were detected; continue close observation.",
        )

    # Strong trajectory with a lower physiological score: ask the structured judge.
    jev_result = ask_jev(risk_context)
    probability = jev_result["needs_additional_escalation"]["probability"]
    posture = jev_result["recommended_response"]["choice"]
    confirms = probability >= 0.60 or posture == "emergency_review"

    if confirms:
        explanation = generate_explanation(
            risk_result={"physiological_score": score, "risk_score": score},
            deterioration_result=trajectory,
            patient_state=patient_state,
            jev_result=jev_result,
        )
        return _base_response(
            news2,
            trajectory,
            should_alert=True,
            priority="high",
            action="clinical_review",
            reason=explanation["summary"],
            source="jev+rag",
            jev_called=True,
            jev_confirmed=True,
            llm_called=explanation.get("mode") == "anthropic",
            jev_detail=jev_result,
            explanation=explanation,
        )

    return _base_response(
        news2,
        trajectory,
        priority="watch",
        action="increased_monitoring",
        reason="Strong trajectory signal detected, but the structured review did not confirm escalation beyond monitoring.",
        source="jev",
        jev_called=True,
        jev_confirmed=False,
        jev_detail=jev_result,
    )
