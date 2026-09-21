"""
Ranks the patient cohort by urgency and suppresses repetitive/non-actionable
alerts rather than re-firing on every reading.
"""
# TODO: maintain last_alert_at per patient; suppress re-firing within a cooldown
# window unless severity has materially increased.
