"""A lightweight, inspectable agent workflow.

The workflow is deliberately small: retrieve evidence -> review structured risk ->
produce an explanation only when escalation requires one. The deterministic risk
engine remains the guardrail and the external model is optional.
"""

from dataclasses import dataclass

from src.agent.jev_judge import ask_jev
from src.agent.nodes import generate_escalation_explanation, retrieve_evidence


@dataclass
class AgentResult:
    jev: dict | None = None
    retrieval: dict | None = None
    explanation: dict | None = None


def run_agent(state, risk_context: dict, patient_context: dict, require_review: bool) -> AgentResult:
    retrieval = retrieve_evidence(state)
    if not require_review:
        return AgentResult(retrieval=retrieval)

    jev = ask_jev(risk_context)
    explanation = generate_escalation_explanation(
        risk_context=risk_context,
        trajectory=risk_context["trajectory"],
        patient_context=patient_context,
        jev_result=jev,
    )
    return AgentResult(jev=jev, retrieval=retrieval, explanation=explanation)
