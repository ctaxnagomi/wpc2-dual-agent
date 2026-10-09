# 01_seed_coding_to_plan.md  (CODING → PLAN / Orchestrator)

> Template. `agent-coding` fills this in after each build and seeds it back.

```json
{
  "seed": "coding_to_plan",
  "project": "WPC2_Zero_Prompts_Demo",
  "build": {
    "source_visual": null,
    "artifacts": [],
    "stack_used": null
  },
  "pre_output_checks": {
    "equality_rules": ["=", "==", "==="],
    "base_statement_compliance": null,
    "stack_matches_approved": null
  },
  "post_output_checks": {
    "equality_rules": ["=", "==", "==="],
    "jev_quality_check": "PENDING_TYPESAFE_API_KEY"
  },
  "policy_risks": [],
  "status": "DRAFT"
}
```
