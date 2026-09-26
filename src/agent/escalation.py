class EscalationState:
    def __init__(self):
        self.active_alert = False
        self.last_alert_level = None

    def reset(self):
        self.active_alert = False
        self.last_alert_level = None


def decide_escalation(
deterioration_result: dict,
risk_result: dict,#from risk_ranking model
escalation_state:EscalationState):
    if deterioration_result.get("deteriorating") is None:
        return {
            "status": "insufficient_data",
            "should_alert": False,
            "reason": "Not enough observations yet"
        }

    if not deterioration_result.get("deteriorating"):
        escalation_state.reset()

        return {
            "status": "ok",
            "should_alert": False,
            "reason": "No active deterioration detected"
        }

    risk_level = risk_result.get("risk_level")

    if escalation_state.active_alert:
        return {
            "status": "suppressed",
            "should_alert": False,
            "reason": "Alert already active",
            "risk_level": risk_level
        }

    escalation_state.active_alert = True
    escalation_state.last_alert_level = risk_level

    return {
        "status": "alert",
        "should_alert": True,
        "risk_level": risk_level,
        "reason": "Deterioration detected with elevated risk"
    }