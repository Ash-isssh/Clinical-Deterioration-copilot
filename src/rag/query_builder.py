def build_clinical_query(state) -> str:
    parts = ["clinical deterioration", "physiological monitoring", "escalation"]

    if state.age is not None:
        parts.append(f"age {state.age}")
    if state.admission_diagnosis:
        parts.append(state.admission_diagnosis)
    if state.relevant_history:
        parts.append(state.relevant_history)
    if state.deterioration:
        parts.extend(state.deterioration.get("concerning_parameters", []))
    if state.news2:
        parts.append(f"news2 {state.news2.get('total', 0)}")
    return " ".join(parts)
