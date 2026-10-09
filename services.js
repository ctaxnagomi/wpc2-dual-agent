// services config (services.js / services.ts / services.jsx / services.tsx)
//
// Dual-Agent + JEV integration for the WPC2 demo.
// The JEV / Typesafe key is read from the environment (JEV_API_KEY).
// Until you provide the key the JEV status stays PENDING_TYPESAFE_API_KEY
// and no JEV check is fabricated.
//
// Later: set JEV_API_KEY in the environment, then re-run a quick test.

const env = typeof process !== "undefined" && process.env ? process.env : {};
const JEV_API_KEY = env.JEV_API_KEY || "";

const services = {
  dual_agent: {
    enabled: true,
    mode: "asynchronous",
    orchestrator: {
      name: "ORCHESTRATOR",
      id: "orchestrator",
      agent_path: ".opencode/agents/orchestrator.md",
      ruleset_path: ".AGENTS/_DUAL-AGENTS/ORCHESTRATOR.md",
      gated_routing: true,
      context_efficient_seeds: true,
      policy_gate: true,
      subagents: ["agent-plan", "agent-coding"],
      seed_dir: ".AGENTS/_DUAL-AGENTS/seeds",
    },
    agents: {
      plan: {
        name: "AGENT-PLAN",
        id: "agent-plan",
        agent_path: ".opencode/agents/agent-plan.md",
        jev_integration: true,
        ruleset_path: ".AGENTS/_DUAL-AGENTS/AGENT-PLAN/JEV_RULESET_AGENT-PLAN.md",
        base_statements: [
          ".AGENTS/_DUAL-AGENTS/AGENT-PLAN/base_statements_stacks.md",
          ".AGENTS/_DUAL-AGENTS/AGENT-PLAN/base_statements_viewports.md",
        ],
      },
      coding: {
        name: "AGENT-CODING",
        id: "agent-coding",
        agent_path: ".opencode/agents/agent-coding.md",
        jev_integration: true,
        ruleset_path: ".AGENTS/_DUAL-AGENTS/AGENT-CODING/JEV_RULESET_AGENT-CODING.md",
      },
    },
    seeds: {
      plan_to_coding: ".AGENTS/_DUAL-AGENTS/seeds/00_seed_plan_to_coding.md",
      coding_to_plan: ".AGENTS/_DUAL-AGENTS/seeds/01_seed_coding_to_plan.md",
    },
    equality_rules: ["=", "==", "==="],
  },
  jev: {
    enabled: true,
    provider: "typesafe",
    api_key_env: "JEV_API_KEY",
    // Disabled placeholder: true once the key is present in the environment.
    api_key_configured: Boolean(JEV_API_KEY),
    status: JEV_API_KEY ? "READY" : "PENDING_TYPESAFE_API_KEY",
    checks: JEV_API_KEY ? "enabled" : "pending",
    dataset: "ctaxnagomi/INSTRUCT_JEV",
    primitives: ["CHOICE", "NOUL", "SCORE"],
    token_efficient: true,
    token_efficient_reduction: true,
  },
  defaults: {
    stack: {
      html: "HTML5",
      css: "SCSS3",
      js: "Vanilla JS",
    },
    model: "deepseek-v4-flash",
    agentic_tool_enable: true,
    tool_calls: true,
    high_quality_output: true,
    prefer_less_token: true,
  },
  tooling: {
    compactDOM: true,
    snapDOM: true,
    html2canvas: true,
    playwrightOrbrowserOSneo: true,
  },
  developer_tags: ["#ctaxnagomi", "#kd_workshop_wpc2", "#krackeddevs"],
};

export default services;
