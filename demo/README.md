# Demo checklist

## Start

Terminal 1:

```bash
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8001
```

Open `http://127.0.0.1:8001/`.

Terminal 2:

```bash
python src/streaming/streamer.py
```

## What to show

- Live patient card updates.
- Recent observations reaching the bounded patient state.
- Trend count rising across multiple vitals.
- NEWS2-derived score and risk level changing.
- Alert escalation.
- Repeated alert suppression.
- Retrieved guideline snippets in the patient state endpoint.
- Accept / dismiss / defer / investigate clinician actions.
- Audit events at `/audit?patient_id=3`.

## Quick reset

```bash
curl -X POST http://127.0.0.1:8001/demo/reset
```

## Video talking points

1. The problem is alarm fatigue, so one abnormal reading should not be enough.
2. Each patient has a state containing static context plus recent streamed vitals.
3. Trend detection compares short windows and looks for several concerning signals together.
4. The deterministic score provides a transparent risk guardrail.
5. RAG supplies local guideline evidence before an escalation explanation is produced.
6. Repeated alerts are suppressed so the clinician does not see the same event on every reading.
7. The clinician can act on the recommendation and that decision is written to the audit trail.
8. The current version is a synthetic-data prototype and is intentionally not presented as a clinical device.
