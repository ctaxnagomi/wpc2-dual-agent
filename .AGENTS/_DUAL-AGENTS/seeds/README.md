# seeds — context-efficient handoff layer

The Orchestrator passes **seeds**, not transcripts, between the two agents.

| File | Direction | Producer | Consumer |
| --- | --- | --- | --- |
| `00_seed_plan_to_coding.md` | PLAN → CODING | `agent-plan` | `agent-coding` |
| `01_seed_coding_to_plan.md` | CODING → PLAN | `agent-coding` | `agent-plan` / Orchestrator |

Rules:
- Keep each seed short (`prefer_less_token`).
- Reference the approved visual by path, do not inline it.
- JEV fields stay `PENDING_TYPESAFE_API_KEY` until `JEV_API_KEY` is set.
