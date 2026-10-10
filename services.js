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
  // Per-agent SDK config (mirrored by .AGENTS/_DUAL-AGENTS/visualization/kdwpc_collect.py SDK_CONF).
  sdk: {
    plan: {
      provider: "opencode",                 // plan runs on the OpenCode session model
      model: "big-pickle",
      api_key_env: null,                    // no external key — OpenCode account model
      agentic_tool_enable: true,
      tool_calls: true,
      high_quality_output: true,
      prefer_less_token: true,
    },
    coding: {
      provider: "openai",                   // openai SDK (pip install openai)
      base_url: "https://litellm.rapidscreen.io/v1",
      api_key_env: "OPENAI_API_KEY",        // env-only — never hardcode
      models: [
        "gpt-5.5", "gpt-5.4", "gpt-5.4-mini", "gpt-5.4-nano",
        "gpt-5.6-sol", "gpt-5.6-luna", "gpt-5.6-terra",
        "gpt-6-sol", "gpt-6-luna",
        "deepseek-v4-flash",                // default
      ],
      default_model: "deepseek-v4-flash",
      agentic_tool_enable: true,
      tool_calls: true,
      high_quality_output: true,
      prefer_less_token: true,
      token_efficient: true,
      imports: ["compactDOM", "snapDOM", "html2canvas", "playwrightOrbrowserOSneo"],
    },
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
