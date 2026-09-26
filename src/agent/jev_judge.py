"""
Wraps TypeSafe's Jev model for a structured trajectory judgment.
Runs fully offline (heuristic fallback) if TYPESAFE_API_KEY isn't set or
the typesafe_sdk package isn't installed, so this module works without
any external account.
"""
import os

TYPESAFE_AVAILABLE = bool(os.getenv("TYPESAFE_API_KEY"))

if TYPESAFE_AVAILABLE:
    try:
        from typesafe_sdk import Choice, Noul, Score, TypeSafeClient
    except ImportError:
        TYPESAFE_AVAILABLE = False

JEV_MODEL = "jev-latest"


def _offline_judgment(risk_context: dict) -> dict:
    """
    Offline stand-in for Jev.

    Uses the same input structure as the real Jev call.
    """

    trajectory = risk_context.get(
        "trajectory",
        {}
    )

    news2 = risk_context.get(
        "news2",
        {}
    )

    news2_score = news2.get(
        "total",
        0
    )

    parameter_count = trajectory.get(
        "parameter_count",
        0
    )

    deteriorating = trajectory.get(
        "deteriorating",
        False
    )

    if deteriorating and parameter_count >= 3:
        posture = "emergency_review"
        sev_score = 3
        probability = 0.85

    elif news2_score >= 7:
        posture = "emergency_review"
        sev_score = 3
        probability = 0.75

    elif deteriorating or parameter_count >= 2:
        posture = "urgent_review"
        sev_score = 2
        probability = 0.65

    elif parameter_count >= 1:
        posture = "increased_monitoring"
        sev_score = 1
        probability = 0.40

    else:
        posture = "routine"
        sev_score = 0
        probability = 0.10

    return {
        "model": "offline-heuristic",

        "needs_additional_escalation": {
            "probability": probability,
        },

        "trajectory_severity": {
            "score": sev_score,
            "confidence": 0.5,
            "probabilities": None,
        },

        "recommended_response": {
            "choice": posture,
            "confidence": 0.5,
            "probabilities": None,
        },

        "usage": {
            "input_tokens": 0,
            "output_tokens": 0,
        },
    }


def ask_jev(risk_context: dict) -> dict:
    if not TYPESAFE_AVAILABLE:
        return _offline_judgment(risk_context)

    questions = {
        "needs_additional_escalation": Noul(
            instructions=(
                "Given the complete patient state, NEWS2 result, and recent "
                "trajectory, is there evidence that the patient warrants "
                "escalation beyond the deterministic NEWS2 response already identified?"
            ),
        ),
        "trajectory_severity": Score(
            instructions=(
                "How concerning is the patient's recent trajectory, considering "
                "the direction and magnitude of changes across multiple vital signs?"
            ),
            criteria=[
                "Stable or no meaningful concerning trajectory.",
                "Mildly concerning trajectory.",
                "Clearly concerning trajectory.",
                "Strongly concerning trajectory requiring close attention.",
            ],
        ),
        "recommended_response": Choice(
            instructions=(
                "Given the patient state, NEWS2 response, and trajectory, which "
                "response posture best fits the evidence? Do not override explicit "
                "NEWS2 emergency or urgent response thresholds."
            ),
            criteria={
                "routine": "Continue routine monitoring; no meaningful additional concern.",
                "increased_monitoring": "Increase monitoring frequency without urgent escalation.",
                "urgent_review": "Prompt clinical review is warranted.",
                "emergency_review": "Immediate/emergency clinical response appears warranted.",
            },
        ),
    }

    try:
        with TypeSafeClient(model=JEV_MODEL) as client:
            response = client.system_one(state=risk_context, questions=questions)
    except Exception:
        return _offline_judgment(risk_context)

    escalation_answer = response.nouls["needs_additional_escalation"]
    trajectory_answer = response.scores["trajectory_severity"]
    response_answer = response.choices["recommended_response"]

    return {
        "model": response.model,
        "needs_additional_escalation": {"probability": escalation_answer.noul},
        "trajectory_severity": {
            "score": trajectory_answer.score,
            "confidence": trajectory_answer.confidence,
            "probabilities": trajectory_answer.probabilities,
        },
        "recommended_response": {
            "choice": response_answer.choice,
            "confidence": response_answer.confidence,
            "probabilities": response_answer.probabilities,
        },
        "usage": {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        },
    }