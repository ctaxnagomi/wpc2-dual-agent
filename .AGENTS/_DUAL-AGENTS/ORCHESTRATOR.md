# ORCHESTRATOR.md
> `.AGENTS/_DUAL-AGENTS/ORCHESTRATOR.md`

---

## Purpose
The Orchestrator runs the **Dual-Agent (PLAN + CODING)** pair in **asynchronous** mode.
It performs gated routing, keeps seeds context-efficient, and enforces the policy gate.

---

## Configuration

```json
{
  "mode": "asynchronous",
  "gated_routing": true,
  "context_efficient_seeds": true,
  "policy_gate": true,
  "agents": {
    "plan":   { "id": "agent-plan",   "ruleset": ".AGENTS/_DUAL-AGENTS/AGENT-PLAN/JEV_RULESET_AGENT-PLAN.md" },
    "coding": { "id": "agent-coding", "ruleset": ".AGENTS/_DUAL-AGENTS/AGENT-CODING/JEV_RULESET_AGENT-CODING.md" }
  },
  "seed_dir": ".AGENTS/_DUAL-AGENTS/seeds",
  "open_code_agents_dir": ".opencode/agents"
}
```

---

## Async Loop

1. **Gate** — confirm approved stack + approved viewports exist in the base statements.
2. **Plan** — `agent-plan` produces the PLAN→CODING seed (`seeds/00_seed_plan_to_coding.md`).
3. **Policy gate** — validate the seed against the base statements and approved stack.
4. **Build** — `agent-coding` implements from the seed and the approved visual.
5. **Verify** — coding post-output checks + CODING→PLAN status seed (`seeds/01_seed_coding_to_plan.md`).
6. **Seed back** — seeds only, never raw transcripts (token efficient).

---

## Policy Gate Rules
- No redesign: `source_of_truth` = approved Excalidraw visual + base statements.
- Stack must match `approved_stack`; viewports must cover mobile / tablet / desktop.
- Apply equality rules (`=`, `==`, `===`) at pre-output and post-output.
- JEV decisions are required when the visual is ambiguous — stop, do not invent.
- If `JEV_API_KEY` is unset → JEV items are **PENDING_TYPESAFE_API_KEY**.

---

## Developer Tags (nest in live project)
```
===Developer===
#ctaxnagomi
#kd_workshop_wpc2
#krackeddevs
===End===
```
