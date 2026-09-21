"""
Immutable audit trail: observation -> retrieved evidence -> reasoning ->
alert -> clinician decision, so any recommendation can be reviewed after the fact.
"""
# TODO: append-only log (file or SQLite table), one row per escalation event
