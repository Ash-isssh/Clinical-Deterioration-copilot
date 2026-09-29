"""Generate an escalation explanation using local templates or an optional LLM.

The default demo path is offline and deterministic. An external LLM is only used
when ANTHROPIC_API_KEY is explicitly supplied.
"""

import json
import os

from src.rag.retriever import retrieve_guidelines

ANTHROPIC_AVAILABLE = bool(os.getenv("ANTHROPIC_API_KEY"))
if ANTHROPIC_AVAILABLE:
    try:
        from anthropic import Anthropic
    except ImportError:  # pragma: no cover
        ANTHROPIC_AVAILABLE = False

MODEL = os.getenv("EXPLAIN_MODEL", "claude-sonnet-4-5-20250929")


def _offline_explanation(risk_result, deterioration_result, patient_state, jev_result, guidelines) -> dict:
    parameters = deterioration_result.get("concerning_parameters", [])
    score = risk_result.get("physiological_score", risk_result.get("risk_score"))
    diagnosis = patient_state.get("static_context", {}).get("admission_diagnosis", "")
    trend_text = ", ".join(parameters) if parameters else "no multi-parameter deterioration trend"

    if jev_result:
        posture = jev_result["recommended_response"]["choice"]
    else:
        posture = "increased_monitoring"

    action = "Immediate clinical review recommended." if posture == "emergency_review" else "Prompt clinical review and repeat observations."
    summary = (
        f"Available-parameter NEWS2-derived score is {score}. "
        f"The recent trajectory shows {trend_text}."
    )
    if diagnosis:
        summary += f" Static admission context: {diagnosis}."

    cited = [
        {
            "source": item["source"],
            "page": item["page"],
            "score": item["score"],
            "text": item["text"][:500],
        }
        for item in guidelines[:2]
    ]

    return {
        "summary": summary,
        "recommended_action": action,
        "retrieved_guidelines": cited,
        "cited_guidelines": [f"{item['source']} p.{item['page']}" for item in guidelines[:2]],
        "mode": "offline-template",
    }


def generate_explanation(risk_result: dict, deterioration_result: dict, patient_state: dict, jev_result: dict | None = None) -> dict:
    score = risk_result.get("physiological_score", risk_result.get("risk_score"))
    query = f"NEWS2 {score} clinical deterioration escalation monitoring"
    guidelines = retrieve_guidelines(query, k=3)

    if not ANTHROPIC_AVAILABLE:
        return _offline_explanation(risk_result, deterioration_result, patient_state, jev_result, guidelines)

    guideline_text = "\n".join(
        f"- {g['source']} page {g['page']}: {g['text']}" for g in guidelines
    )
    prompt = f"""You are a clinical decision-support prototype.

"
"Use only the supplied patient state and retrieved text. Do not diagnose.

"
f"Patient: {json.dumps(patient_state)}
"
f"Risk score: {score}
"
f"Trajectory: {json.dumps(deterioration_result)}
"
f"Retrieved guidance:
{guideline_text}

"
"Return JSON with summary, recommended_action, and cited_guidelines."""

    try:  # pragma: no cover - external service path
        client = Anthropic()
        response = client.messages.create(
            model=MODEL,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = "".join(block.text for block in response.content if block.type == "text").strip()
        parsed = json.loads(raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip())
        return {
            "summary": parsed.get("summary", ""),
            "recommended_action": parsed.get("recommended_action", ""),
            "retrieved_guidelines": guidelines,
            "cited_guidelines": parsed.get("cited_guidelines", []),
            "mode": "anthropic",
        }
    except Exception:
        return _offline_explanation(risk_result, deterioration_result, patient_state, jev_result, guidelines)
