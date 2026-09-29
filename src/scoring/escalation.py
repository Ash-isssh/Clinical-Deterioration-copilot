"""Compatibility wrapper for the final escalation policy.

The implementation lives in ``src.agent.escalation`` because escalation is the
controlled agent/orchestration stage. This module keeps the old import path valid.
"""

from src.agent.escalation import (
    NEWS2_EMERGENCY_THRESHOLD,
    NEWS2_URGENT_THRESHOLD,
    decide_escalation,
)

__all__ = [
    "NEWS2_EMERGENCY_THRESHOLD",
    "NEWS2_URGENT_THRESHOLD",
    "decide_escalation",
]
