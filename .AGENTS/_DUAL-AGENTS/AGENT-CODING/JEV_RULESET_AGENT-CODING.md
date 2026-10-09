# JEV_RULESET_AGENT-CODING.md
> Copy this into: `.AGENTS/_DUAL-AGENTS/AGENT-CODING/JEV_RULESET_AGENT-CODING.md`

---

## Purpose
This file focuses on coding compliance, accuracy, and quality.  
It receives seeds from AGENT-PLAN + JEV and communicates sub-parallel during development.

---

## Core Rules for AGENT-CODING

```json
{
  "source_of_truth": "Approved Excalidraw visual + base_statements from AGENT-PLAN",
  "must_match_visual": true,
  "no_redesign": true,
  "responsive": true,
  "use_jev_for_quality_checks": true
}
```

---

## Pre / Post Output Checks (Mandatory)

```json
{
  "pre_output": {
    "apply_equality_rules": ["=", "==", "==="],
    "check_compliance_with_base_statements": true,
    "confirm_stack_matches_approved": true
  },
  "post_output": {
    "apply_equality_rules": ["=", "==", "==="],
    "run_quality_check_via_jev": true,
    "seed_status_to_orchestrator": true
  }
}
```

---

## Required Tooling

```json
{
  "imports": ["compactDOM", "snapDOM", "html2canvas", "playwrightOrbrowserOSneo"],
  "used_for": {
    "compactDOM": "reduce the built/rendered DOM to a token-efficient structure for diffing",
    "snapDOM": "capture the rendered DOM tree of the Excalidraw canvas / built page",
    "html2canvas": "rasterize a rendered target to PNG for the visual diff",
    "playwrightOrbrowserOSneo": "open and drive the Excalidraw scene / preview page in the browser"
  },
  "agentic_tool_enable": true,
  "tool_calls": true,
  "token_efficient": true,
  "preferred_model": "deepseek-v4-flash"
}
```

---

## Excalidraw Source Intake (parser step)

Before coding, parse the approved visual (it is a JSON scene); do not code from a screenshot.

```json
{
  "step": "excalidraw_intake",
  "input": "source_visual from the PLAN→CODING seed (.excalidraw path)",
  "read_via": "read (JSON)",
  "validate": ["type === 'excalidraw'", "Array.isArray(elements)"],
  "extract_per_element": ["id", "type", "x", "y", "width", "height", "text", "frameId", "groupIds"],
  "group_by": "frame (type === 'frame')",
  "order": "frame order, then top→bottom (y), then left→right (x)",
  "emit": "visual_outline { frames: [{ name, elements: [{ type, label, box }] }] }"
}
```

- Every element in the build must trace to an element in `elements[]` (`no_redesign`).
- Never invent elements; if the scene is ambiguous → stop and request a JEV decision.

---

## Browser Capture Flow (visual verification)

Use this to render the scene and compare it against the built page.

```json
{
  "flow": "browser_capture",
  "tool": "playwrightOrbrowserOSneo",
  "steps": [
    "open the Excalidraw scene / built preview page in the browser",
    "snapDOM → capture the rendered DOM tree of the target",
    "html2canvas → rasterize the target to PNG",
    "compactDOM → reduce the DOM to a token-efficient structure",
    "diff built page vs captured reference → list deltas",
    "feed the diff into the JEV quality check (post_output)"
  ],
  "status": "PENDING_TYPESAFE_API_KEY (JEV step only)"
}
```

---

## Communication with AGENT-PLAN + Orchestrator

- Fetch viewports and stacks from AGENT-PLAN
- Report progress and any policy risk back to Orchestrator
- If visual is ambiguous → stop and request new JEV decision (do not invent)

---

## Developer Tags
```
===Developer===
#ctaxnagomi
#kd_workshop_wpc2
#krackeddevs
===End===
```
