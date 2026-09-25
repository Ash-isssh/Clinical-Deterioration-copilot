"""
Generates the plain-language, evidence-grounded escalation explanation.
Runs fully offline (template-based) if ANTHROPIC_API_KEY isn't set or the
anthropic package isn't installed — no external account required to test.
"""
import json
import os

ANTHROPIC_AVAILABLE = bool(os.getenv("ANTHROPIC_API_KEY"))
if ANTHROPIC_AVAILABLE:
    try:
        from anthropic import Anthropic
    except ImportError:
        ANTHROPIC_AVAILABLE = False

MODEL = os.getenv("EXPLAIN_MODEL", "claude-sonnet-4-5-20250929")

try:
    from src.rag.retriever import retrieve_guidelines
except (ImportError, NotImplementedError):
    retrieve_guidelines = None


def _fallback_retrieve(query: str, k: int = 3) -> list[dict]:
    return [{
        "text": (
            "NEWS2 aggregate score of 7 or more indicates a high-risk patient "
            "requiring urgent or emergency clinical review, regardless of "
            "which individual parameter is driving the score."
        ),
        "source": "NEWS2 guideline (fallback, no retriever configured)",
    }]


def _get_guidelines(query: str) -> list[dict]:
    fn = retrieve_guidelines or _fallback_retrieve
    try:
        return fn(query, k=3)
    except Exception:
        return _fallback_retrieve(query, k=3)


def _offline_explanation(risk_result, deterioration_result, jev_result, guidelines) -> dict:
    """Template-based explanation, no LLM call, no API key needed."""
    trends = deterioration_result.get("trends", {})
    worsening = [f"{param} {direction}" for param, direction in trends.items()
                 if direction in ("increasing", "decreasing")]
    trend_text = ", ".join(worsening) if worsening else "no clear multi-parameter trend"

    jev_text = ""
    if jev_result:
        jev_text = f" Trajectory review flagged this as '{jev_result['recommended_response']['choice']}'."

    summary = (
        f"NEWS2 score of {risk_result.get('risk_score')} "
        f"({risk_result.get('risk_level')} risk), driven by: {trend_text}.{jev_text}"
    )
    action = (
        "Immediate clinical review recommended." if risk_result.get("risk_score", 0) >= 7
        else "Increase observation frequency and reassess."
    )

    return {
        "summary": summary,
        "recommended_action": action,
        "retrieved_guidelines": guidelines,
        "cited_guidelines": [guidelines[0]["source"]] if guidelines else [],
    }


def generate_explanation(
    risk_result: dict,
    deterioration_result: dict,
    patient_state: dict,
    jev_result: dict | None = None,
) -> dict:
    query = f"NEWS2 score {risk_result.get('risk_score')} escalation guideline"
    guidelines = _get_guidelines(query)

    if not ANTHROPIC_AVAILABLE:
        return _offline_explanation(risk_result, deterioration_result, jev_result, guidelines)

    guideline_text = "\n".join(f"- ({g['source']}): {g['text']}" for g in guidelines)
    jev_note = ""
    if jev_result:
        jev_note = (
            f"\nA structured trajectory review (Jev) rated trajectory severity "
            f"'{jev_result['trajectory_severity']['score']}' and recommended "
            f"posture: {jev_result['recommended_response']['choice']}."
        )

    prompt = f"""You are assisting a clinical deterioration monitoring system.
A patient has been flagged for escalation. Write a short, plain-language,
evidence-grounded explanation a clinician can quickly read and act on.

Patient context: {json.dumps(patient_state.get("static_context", {}))}
Latest vitals: {json.dumps(patient_state.get("latest_vitals", {}))}
NEWS2 score: {risk_result.get("risk_score")} (risk level: {risk_result.get("risk_level")})
Detected trend: {json.dumps(deterioration_result)}
{jev_note}

Relevant guideline excerpts:
{guideline_text}

Respond ONLY with valid JSON, no other text, in this exact shape:
{{
  "summary": "one or two sentence plain-language explanation of why this patient is being escalated",
  "recommended_action": "short, concrete next step for the clinician",
  "cited_guidelines": ["exact source strings you relied on from the excerpts above"]
}}"""

    try:
        client = Anthropic()
        response = client.messages.create(model=MODEL, max_tokens=400,
                                           messages=[{"role": "user", "content": prompt}])
        raw_text = "".join(b.text for b in response.content if b.type == "text")
        cleaned = raw_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        parsed = json.loads(cleaned)
        return {
            "summary": parsed.get("summary", ""),
            "recommended_action": parsed.get("recommended_action", ""),
            "retrieved_guidelines": guidelines,
            "cited_guidelines": parsed.get("cited_guidelines", []),
        }
    except Exception:
        return _offline_explanation(risk_result, deterioration_result, jev_result, guidelines)