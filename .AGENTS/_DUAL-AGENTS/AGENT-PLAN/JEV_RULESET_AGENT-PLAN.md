# JEV_RULESET_AGENT-PLAN.md
> Copy this into: `.AGENTS/_DUAL-AGENTS/AGENT-PLAN/JEV_RULESET_AGENT-PLAN.md`

---

## Purpose
This base statements file is for compliance in following/obeying the guidelines to AGENTS-PLAN + JEV.  
It also seeds other AGENTS during Asynchronous process to ensure AGENT-CODING complies with the guidelines for outputs.

---

## Base Statements (Organic Source of Truth)

### base_statements_stacks.md
```json
{
  "default_stack": {
    "html": "HTML5",
    "css": "SCSS3",
    "js": "Vanilla JS"
  },
  "note": "Always suggest HTML5 + SCSS3 + Vanilla JS first. If user chooses a different stack, obey and record it here.",
  "allowed_overrides": ["Next.js", "React", "Vue", "Svelte", "Tailwind", "TypeScript"]
}
```

### base_statements_viewports.md
```json
{
  "primary_viewports": ["mobile", "tablet", "desktop"],
  "breakpoints": {
    "mobile": "max-width: 640px",
    "tablet": "641px - 1024px",
    "desktop": "min-width: 1025px"
  },
  "rule": "All pages generated from Excalidraw must be fully responsive across these viewports."
}
```

---

## Required Prerequisites (must exist in every base_statement)

### 1.a Equality Rules
```json
{
  "rule": "Use =, ==, and === during Asynchronous process/state",
  "when": "Every time you initiate pre-output and post-output",
  "purpose": "Ensure guidelines using JEV functions are efficient and accurate"
}
```

### 1.b Agentic Tooling + Model
```json
{
  "imports": ["compactDOM", "snapDOM", "html2canvas", "playwrightOrbrowserOSneo"],
  "defaults": {
    "agentic_tool_enable": true,
    "tool_calls": true,
    "high_quality_output": true,
    "prefer_less_token": true
  },
  "preferred_model": "deepseek-v4-flash",
  "token_efficient_reduction": true
}
```

---

## Excalidraw Source Intake (parser step)

The approved visual is a `.excalidraw` file — a **JSON scene**. Parse the file; do not guess from a screenshot.

```json
{
  "step": "excalidraw_intake",
  "input": "path to the approved .excalidraw (e.g. kd_wpc_2-*.excalidraw)",
  "read_via": "read (the file is JSON)",
  "validate": ["type === 'excalidraw'", "Array.isArray(elements)"],
  "extract_per_element": ["id", "type", "x", "y", "width", "height", "text", "frameId", "groupIds"],
  "group_by": "frame (type === 'frame') → frame.name becomes the section name",
  "order": "frame order, then top→bottom (y), then left→right (x)",
  "emit": "visual_outline { frames: [{ name, elements: [{ type, label, box }] }] }",
  "equality_checks": ["element.type === expected", "frame membership ==="]
}
```

Rules:
- Read and parse the scene before planning; never invent elements that are not in `elements[]`.
- Frames = sections; text elements = labels/copy.
- Store the compact `visual_outline` in the PLAN→CODING seed under `source_visual`. Reference the file path, do not inline the raw scene.

---

## Imports / Tools (explicit reference)

`defaults.agentic_tool_enable` and `defaults.tool_calls` are `true`; all `tooling.*` flags are on.
The four named tools and what the agents use them for:

```json
{
  "imports": ["compactDOM", "snapDOM", "html2canvas", "playwrightOrbrowserOSneo"],
  "used_for": {
    "compactDOM": "reduce a rendered DOM to a token-efficient structure for planning and diffing",
    "snapDOM": "capture the rendered DOM tree of the Excalidraw canvas / built page",
    "html2canvas": "rasterize a rendered target to PNG for visual diff",
    "playwrightOrbrowserOSneo": "open and drive the Excalidraw scene / preview page in the browser"
  },
  "agentic_tool_enable": true,
  "tool_calls": true
}
```

---

## JEV Guidelines Reference
- Dataset: `ctaxnagomi/INSTRUCT_JEV` (compiled from Typesafe AI documentation)
- Base Statements = organic (human-written source of truth)
- JEV Statements = generated from base statements using CHOICE / NOUL / SCORE
- JEV is token efficient

---

## Developer Tags (nest these in live project)
```
===Developer===
#ctaxnagomi
#kd_workshop_wpc2
#krackeddevs
===End===
```
