"""Optional structured trajectory judge with a deterministic offline fallback."""

import os

TYPESAFE_AVAILABLE = bool(os.getenv("TYPESAFE_API_KEY"))

if TYPESAFE_AVAILABLE:
    try:
        from typesafe_sdk import Choice, Noul, Score, TypeSafeClient
    except ImportError:  # pragma: no cover - optional integration
        TYPESAFE_AVAILABLE = False

JEV_MODEL = os.getenv("JEV_MODEL", "jev-latest")


def _offline_judgment(risk_context: dict) -> dict:
    trajectory = risk_context.get("trajectory", {})
    news2 = risk_context.get("news2", {})
    score = news2.get("total", 0)
    count = trajectory.get("parameter_count", 0)
    deteriorating = trajectory.get("deteriorating")

    if score >= 7 or (deteriorating and count >= 4):
        posture, severity, probability = "emergency_review", 3, 0.90
    elif deteriorating and count >= 3:
        posture, severity, probability = "emergency_review", 3, 0.85
    elif score >= 5 or count >= 2:
        posture, severity, probability = "urgent_review", 2, 0.70
    elif score >= 1 or count >= 1:
        posture, severity, probability = "increased_monitoring", 1, 0.40
    else:
        posture, severity, probability = "routine", 0, 0.10

    return {
        "model": "offline-heuristic",
        "needs_additional_escalation": {"probability": probability},
        "trajectory_severity": {"score": severity, "confidence": 0.80, "probabilities": None},
        "recommended_response": {"choice": posture, "confidence": 0.80, "probabilities": None},
        "usage": {"input_tokens": 0, "output_tokens": 0},
    }


def ask_jev(risk_context: dict) -> dict:
    if not TYPESAFE_AVAILABLE:
        return _offline_judgment(risk_context)

    questions = {
        "needs_additional_escalation": Noul(
            instructions=(
                "Review the supplied deterministic evidence. Decide whether the "
                "recent trajectory warrants additional escalation beyond the current response."
            )
        ),
        "trajectory_severity": Score(
            instructions=(
                "Rate how concerning the recent multi-parameter trajectory is."
            ),
            criteria=[
                "Stable or not concerning",
                "Mildly concerning",
                "Clearly concerning",
                "Strongly concerning",
            ],
        ),
        "recommended_response": Choice(
            instructions="Choose a response posture without overriding deterministic emergency guardrails.",
            criteria={
                "routine": "Continue routine monitoring.",
                "increased_monitoring": "Increase monitoring frequency.",
                "urgent_review": "Prompt clinical review.",
                "emergency_review": "Immediate/emergency clinical response.",
            },
        ),
    }

    try:  # pragma: no cover - external service path
        with TypeSafeClient(model=JEV_MODEL) as client:
            response = client.system_one(state=risk_context, questions=questions)
    except Exception:
        return _offline_judgment(risk_context)

    return {
        "model": response.model,
        "needs_additional_escalation": {"probability": response.nouls["needs_additional_escalation"].noul},
        "trajectory_severity": {
            "score": response.scores["trajectory_severity"].score,
            "confidence": response.scores["trajectory_severity"].confidence,
            "probabilities": response.scores["trajectory_severity"].probabilities,
        },
        "recommended_response": {
            "choice": response.choices["recommended_response"].choice,
            "confidence": response.choices["recommended_response"].confidence,
            "probabilities": response.choices["recommended_response"].probabilities,
        },
        "usage": {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        },
    }
