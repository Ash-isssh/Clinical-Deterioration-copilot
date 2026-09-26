from src.state.state_manager import get_or_create_patient_state
from src.detection.trend_detection import detect_trends
from src.detection.deterioration_detecter import detect_deterioration


def process_vital(observation):

    patient_id = observation.patient_id

    # Get existing state or create it for the first observation
    state = get_or_create_patient_state(patient_id)

    # Store the new vital
    vital_data = observation.model_dump()
    state.add_vital(vital_data)

    # Get recent observations
    recent_vitals = state.get_recent_vitals()

    # Detect trends
    trends = detect_trends(recent_vitals)

    # Detect multi-parameter deterioration
    deterioration_result = detect_deterioration(trends)

    # Store latest analysis in patient state
    state.update_analysis(
        trends=trends,
        deterioration=deterioration_result
    )

    return state, trends, deterioration_result