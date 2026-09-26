PatientState / latest vital
             │
             ▼
        NEWS2 Engine
             │
      ┌──────┼──────┐
      ▼      ▼      ▼
      RR    SpO2    SBP
      │      │       │
      ├──────┼───────┤
      ▼      ▼       ▼
    Pulse  Conscious Temp
             │
             ▼
       component scores
             │
             ▼
        NEWS2 TOTAL
             │
             ▼
      response trigger
             │
             ▼
     Risk Ranking + Jev



## NEXT COMPONENT — risk_ranking.py

Now we combine two independent signals:

                    Current patient
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
         NEWS2 result          Team 1 result
             │                       │
             │                deterioration
             │                   trends
             ▼                       ▼
             └───────────┬───────────┘
                         ▼
                  Risk Ranking
                         │
                         ▼
                       Jev

## jev
 build_risk_context()     : total information from risk ranking file
              │
              ▼
        jev_decision.py
              │
       ┌──────┼────────┐
       ▼      ▼        ▼
     Choice  Noul     Score
       │      │        │
       └──────┼────────┘
              ▼
        Jev result
              │
              ▼
    deterministic guardrails


example:

                         risk_context
                              │
                              ▼
                       escalation.py
                              │
               ┌──────────────┼──────────────┐
               │              │              │
             0–4            5–6             7+
               │              │              │
            FAST PATH      URGENT         JEV PATH
               │              │              │
            No Jev          No Jev          Jev
            No LLM          No LLM           │
               │              │        ┌─────┴─────┐
               │              │        ▼           ▼
               │              │    confirms     doesn't
               │              │    concern      confirm
               │              │        │           │
               │              │        ▼           ▼
               │              │       LLM        STILL
               │              │       + RAG     EMERGENCY
               └──────────────┴──────────┬────────┘
                                         ▼
                                  final decision