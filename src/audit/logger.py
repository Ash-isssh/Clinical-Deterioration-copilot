"""Append-only JSONL audit log for observations, evidence, alerts and decisions."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[2]
AUDIT_FILE = BASE_DIR / "data" / "audit" / "events.jsonl"


def append_event(event_type: str, patient_id: int | None, payload: dict[str, Any]) -> dict:
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "patient_id": patient_id,
        "payload": payload,
    }
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, default=str) + "\n")
    return event


def read_events(patient_id: int | None = None) -> list[dict]:
    if not AUDIT_FILE.exists():
        return []
    events = []
    with AUDIT_FILE.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            event = json.loads(line)
            if patient_id is None or event.get("patient_id") == patient_id:
                events.append(event)
    return events
