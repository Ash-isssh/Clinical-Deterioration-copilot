# Final Technical Documentation

## 1. Problem

The system addresses the hackathon problem of monitoring a stream of patient vitals, maintaining an evolving patient state, detecting meaningful multi-parameter deterioration, reducing repeated alarms, retrieving supporting clinical context, and giving the clinician a clear escalation explanation.

## 2. Final architecture

```text
streamer -> FastAPI -> PatientState
                         |
                         +-> trend detection
                         +-> deterioration detection
                         +-> NEWS2-derived scoring
                         +-> risk context
                         +-> local RAG retrieval
                         +-> escalation policy / optional Jev
                         +-> explanation
                         +-> clinician action
                         +-> JSONL audit
                         +-> WebSocket dashboard
```

## 3. Data flow

### Static context

`data/patient_profiles/patient_demographics.csv` is loaded once at process startup. It supplies age, gender, admission diagnosis, relevant history, medications, recent labs, recent procedures and clinical notes.

### Streamed context

`data/raw/synthetic_vitals.csv` contains the synthetic vital observations. The replay script sends one observation at a time to `POST /vitals`.

### Stateful processing

For each accepted observation, the pipeline:

1. validates the value ranges;
2. ignores duplicate timestamps;
3. accepts out-of-order observations and stores the recent history by timestamp;
4. calculates rolling-window changes;
5. counts concerning directions across parameters;
6. calculates the available-parameter NEWS2-derived score;
7. builds the risk context;
8. retrieves local guideline evidence when enough history exists;
9. decides whether to alert;
10. suppresses repeated alerts with the same priority/action/source inside the suppression window;
11. records the result in the audit log.

## 4. RAG

The repository includes a prebuilt JSON chunk index under `data/guidelines/index.json` so the API does not perform PDF parsing for every observation. Retrieval is intentionally simple and inspectable: query tokens are matched against the local text chunks and the top matches are returned with source and page information.

## 5. Agent path

The project keeps the deterministic risk layer separate from the optional agent components. The structured Jev integration is only consulted for strong trajectory cases or emergency scores. The deterministic guardrail remains responsible for preserving high-risk states. The explanation layer can run completely offline using the retrieved evidence.

## 6. Clinician loop

The dashboard exposes four actions:

- Accept
- Dismiss
- Defer
- Investigate

Each action is recorded with a timestamp and optional note.

## 7. Audit trail

`src/audit/logger.py` writes JSON Lines records for processed observations, generated alerts, rejected stream records, clinician decisions and demo resets. This provides a simple post-hoc record for the presentation and testing.

## 8. Testing

The final test suite checks the scoring functions, trend detector, escalation policy, pipeline integration, stream edge cases and repeated-alert suppression.

Run:

```bash
python -m pytest -q
```

The completed local run contains 20 passing tests.

## 9. Known limitations

This is a hackathon prototype using synthetic data. Trend thresholds have not been clinically validated. The NEWS2-derived calculation intentionally uses only the physiological inputs present in the prototype rather than inventing unavailable measurements. The RAG retriever is keyword based. External model integrations are optional and are not needed to reproduce the demo.
