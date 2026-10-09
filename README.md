# WPC2 Dual-Agent Kit

Dual-Agent (**AGENT-PLAN** + **AGENT-CODING**) + **JEV** ruleset scaffold for the WPC2 workshop.

The two agents run **asynchronously**, routed by an **Orchestrator** with gated routing, a policy
gate, and context-efficient seeds.

## Structure

```
.AGENTS/
└── _DUAL-AGENTS/
    ├── ORCHESTRATOR.md                      # async loop, gated routing, policy gate
    ├── MEMORY_SCOPE.md                       # per-project memory scope + salience gate
    ├── AGENT-PLAN/
    │   ├── JEV_RULESET_AGENT-PLAN.md        # planning ruleset
    │   ├── base_statements_stacks.md        # organic stack source of truth
    │   └── base_statements_viewports.md     # organic viewport source of truth
    ├── AGENT-CODING/
    │   └── JEV_RULESET_AGENT-CODING.md      # coding ruleset
    └── seeds/
        ├── 00_seed_plan_to_coding.md        # PLAN → CODING handoff
        └── 01_seed_coding_to_plan.md        # CODING → PLAN status
.opencode/
├── opencode.jsonc                           # loads both rulesets as instructions
└── agents/
    ├── agent-plan.md                        # AGENT-PLAN subagent
    ├── agent-coding.md                      # AGENT-CODING subagent
    └── orchestrator.md                      # ORCHESTRATOR
services.js                                  # Dual-Agent + JEV config
```

## Defaults

- Stack: **HTML5 + SCSS3 + Vanilla JS** (overrides allowed: Next.js, React, Vue, Svelte, Tailwind, TypeScript).
- Viewports: mobile `max-width: 640px`, tablet `641px–1024px`, desktop `min-width: 1025px`.
- Equality rules (`=`, `==`, `===`) at pre-output and post-output.
- Tooling: `compactDOM`, `snapDOM`, `html2canvas`, `playwrightOrbrowserOSneo`.

## JEV

`services.js` reads the Typesafe key from the environment variable `JEV_API_KEY`.
Until it is set, `jev.status` is `PENDING_TYPESAFE_API_KEY` and JEV checks are not fabricated.

```bash
# set the key, then reload
export JEV_API_KEY=...
```

- Dataset: `ctaxnagomi/INSTRUCT_JEV`
- Primitives: `CHOICE`, `NOUL`, `SCORE`

## Memory (DGUI-HyperMem)

Long-term memory for this kit lives in the **`wpc2-dual-agent`** scope (not the shared
`default`). See [`MEMORY_SCOPE.md`](.AGENTS/_DUAL-AGENTS/MEMORY_SCOPE.md).

> **Gate:** DGUI-HyperMem only surfaces memories with JEV `salience ≥ ~3.0`. Write one
> rich, high-signal `project` memory and verify `active ≥ 1` afterwards — low-salience
> notes are stored but invisible to search.

## Developer Tags

```
===Developer===
#ctaxnagomi
#kd_workshop_wpc2
#krackeddevs
===End===
```
