"""Small agent nodes used by the controlled escalation flow."""

from src.rag.retriever import retrieve_for_patient
from src.agent.llm_explain import generate_explanation


def retrieve_evidence(state) -> dict:
    return retrieve_for_patient(state, k=3)


def generate_escalation_explanation(risk_context: dict, trajectory: dict, patient_context: dict, jev_result=None) -> dict:
    return generate_explanation(
        risk_result={
            "physiological_score": risk_context["news2"].get("total"),
            "risk_score": risk_context["news2"].get("total"),
        },
        deterioration_result=trajectory,
        patient_state=patient_context,
        jev_result=jev_result,
    )
