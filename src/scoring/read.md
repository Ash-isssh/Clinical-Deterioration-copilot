# Scoring and escalation flow

```text
PatientState / latest vital
        |
        +--> available-parameter NEWS2-derived score
        |
        +--> trend + deterioration evidence
        |
        v
   risk_context
        |
        v
 controlled escalation policy
        |
   +----+------------------------+
   |    |                        |
 low/watch       NEWS2 5-6      NEWS2 7+
   |             urgent         emergency guardrail
   |                |                 |
   +----------------+-----------------+
                    |
            strong trajectory?
                    |
                 optional Jev
                    |
             evidence-grounded
                explanation
```

The final implementation is deterministic by default. The optional Jev and Anthropic integrations are only enabled when their environment keys are provided.
