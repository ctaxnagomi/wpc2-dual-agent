#!/usr/bin/env python3
"""KD-WPC JEV suggestion bridge — turn a per-agent base statement into JEV statements.

The dashboard (kdwpc.html) cannot hold the Typesafe key, and never should. This tiny
localhost bridge owns the key (env-only, mirroring the kit rules) and is the only
thing that talks to the upstream JEV API (`https://api.typesafe.ai/v1/systemone`).

Endpoints (http://localhost:8778)
  GET  /health
       -> {"key": "set"|"missing"|"file", "model": "jev-latest", "bridge": "kdwpc-jev"}
  POST /suggest   {"agent": "plan"|"coding", "base_statement": "..."}
       -> calls System One with CHOICE / NOUL / SCORE questions (per-agent, aligned
          with the agent's own JEV_RULESET), saves the generated jev_statements into
          data/kdwpc_live.json (atomic), returns the answers.

The key is read, in order, from JEV_API_KEY, TYPESAFE_API_KEY, or the odv.py secret
file ~/.pi/agent/secrets/typesafe_api_key. Never from the repo, never sent to the
browser (CORS is open only so *this page* can POST its statement locally).

Run it alongside the dashboard:
  python kdwpc_jev.py            # http://localhost:8778  (or `run.cmd` starts it)
"""
import json
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError

HERE = os.path.dirname(os.path.realpath(__file__))
DATA_DEST = os.path.join(HERE, "data")
LIVE_JSON = os.path.join(DATA_DEST, "kdwpc_live.json")
PORT = int(os.environ.get("KDWPC_JEVPORT", "8778"))
UPSTREAM = os.environ.get("JEV_ENDPOINT", "https://api.typesafe.ai").rstrip("/") + "/v1/systemone"
MODEL = os.environ.get("JEV_MODEL", "jev-latest")

# Question templates, one set per agent, matching that agent's own JEV role.
# plan  :: statement gen — base statements -> CHOICE / NOUL / SCORE (see JEV_RULESET_AGENT-PLAN.md)
# coding:: quality checks — browser-capture diff -> verdicts (see JEV_RULESET_AGENT-CODING.md)
PLAN_STACK = ["HTML5 + SCSS3 + Vanilla JS", "Next.js", "React", "Vue", "Svelte", "Tailwind", "TypeScript",
              "Three.js", "Canvas / WebGL", "(keep current stack)"]
CODING_CONSTRAINTS = ["must_match_visual", "no_redesign", "responsive", "use_jev_for_quality_checks",
                      "source_of_truth: approved .excalidraw", "new tooling / stack"]
SCORE_LEVELS = ["trivial / no change", "small change", "moderate change", "significant re-plan / re-build"]


def agent_questions(agent):
    """Build the CHOICE / NOUL / SCORE question set for one agent."""
    if agent == "plan":
        return {
            "stack_choice": {
                "type": "choice",
                "instructions": "Which primary stack or tooling does this base statement imply or add?",
                "criteria": {s: s for s in PLAN_STACK},
            },
            "base_change_noul": {
                "type": "noul",
                "instructions": "Does this base statement CHANGE or EXTEND the existing base statements"
                                " (stacks/viewports/constraints), so the = == === equality checks must run"
                                " on pre-output and post-output?",
            },
            "impact_score": {
                "type": "score",
                "instructions": "How much does this base statement change the current approved plan?",
                "criteria": SCORE_LEVELS,
            },
        }
    return {  # coding
        "constraint_choice": {
            "type": "choice",
            "instructions": "Which existing coding constraint is this base statement most related to?",
            "criteria": {c: c for c in CODING_CONSTRAINTS},
        },
        "coverage_noul": {
            "type": "noul",
            "instructions": "Given the approved Excalidraw visual + current base statements: is this new"
                            " requirement fully covered by the source of truth, or does it need a NEW JEV"
                            " decision before coding starts?",
        },
        "complexity_score": {
            "type": "score",
            "instructions": "Implementation complexity of adding this to the current build?",
            "criteria": SCORE_LEVELS,
        },
    }


def key():
    k = (os.environ.get("JEV_API_KEY") or os.environ.get("TYPESAFE_API_KEY") or "").strip()
    if k:
        return k, "set"
    p = os.path.join(os.path.expanduser("~"), ".pi", "agent", "secrets", "typesafe_api_key")
    if os.path.exists(p):
        k = open(p).read().strip()
        if k:
            return k, "file"
    return None, "missing"


def systemone(api_key, state, questions):
    body = json.dumps({"state": state, "model": MODEL, "questions": questions}).encode()
    req = Request(UPSTREAM, data=body,
                  headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=60) as r:
            return json.load(r)
    except HTTPError as e:
        return {"error": f"upstream HTTP {e.code}: {e.read().decode(errors='replace')[:300]}"}
    except Exception as e:  # noqa: BLE001 - surface a readable error to the dashboard
        return {"error": str(e)}


CODING_MODELS = ["gpt-5.5", "gpt-5.4", "gpt-5.4-mini", "gpt-5.4-nano",
                 "gpt-5.6-sol", "gpt-5.6-luna", "gpt-5.6-terra",
                 "gpt-6-sol", "gpt-6-luna", "deepseek-v4-flash"]  # keep in sync with kdwpc_collect.py / services.js

def coding_key_status():
    return "SET · env-only (OPENAI_API_KEY)" if os.environ.get("OPENAI_API_KEY") \
        else "missing · env-only (OPENAI_API_KEY)"

def load_live():
    if os.path.isfile(LIVE_JSON):
        try:
            return json.load(open(LIVE_JSON, encoding="utf-8")) or {}
        except Exception:
            return {}
    return {}

def save_json(live):
    os.makedirs(DATA_DEST, exist_ok=True)
    tmp = LIVE_JSON + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(live, f, indent=2)
    os.replace(tmp, LIVE_JSON)

def save_sdk(agent, model=None):
    live = load_live()
    live.setdefault("agents", {}).setdefault(agent, {})
    sdk = live["agents"][agent].setdefault("sdk", {})
    sdk["provider"] = "openai SDK"
    sdk["base_url"] = "https://litellm.rapidscreen.io/v1"
    sdk["key_env"] = "OPENAI_API_KEY"
    sdk["models"] = list(CODING_MODELS)
    sdk["key_status"] = coding_key_status()
    sdk["agentic_tool_enable"] = True
    sdk["tool_calls"] = True
    sdk["high_quality_output"] = True
    sdk["prefer_less_token"] = True
    sdk["token_efficient"] = True
    if model:
        if model not in CODING_MODELS:
            return None, f"model must be one of: {', '.join(CODING_MODELS)}"
        sdk["model"] = model
    if "model" not in sdk:
        sdk["model"] = "deepseek-v4-flash"
    save_json(live)
    return live["agents"][agent]["sdk"], None

def save_live(agent, base_statement, resp):
    os.makedirs(DATA_DEST, exist_ok=True)
    live = {}
    if os.path.isfile(LIVE_JSON):
        try:
            live = json.load(open(LIVE_JSON, encoding="utf-8"))
        except Exception:
            live = {}
    live.setdefault("agents", {}).setdefault(agent, {})
    live["agents"][agent]["jev_suggestion"] = {
        "base_statement": base_statement,
        "model": resp.get("model") or MODEL,
        "statements": resp.get("answers") or {},
        "raw": resp.get("error") or None,
        "ts": int(__import__("time").time()),
    }
    if resp.get("error"):
        live["agents"][agent]["jev_suggestion"]["status"] = "ERROR"
    else:
        live["agents"][agent]["jev_suggestion"]["status"] = "GENERATED"
    tmp = LIVE_JSON + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(live, f, indent=2)
    os.replace(tmp, LIVE_JSON)
    return live["agents"][agent]["jev_suggestion"]


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/health":
            api_key, src = key()
            self._json(200, {"bridge": "kdwpc-jev", "key": "set" if api_key else "missing", "key_source": src, "model": MODEL})
        elif path == "/sdk":
            live = load_live()
            ag = live.get("agents") or {}
            sdk = {
                "plan":   (ag.get("plan") or {}).get("sdk") or {"provider": "opencode", "model": "big-pickle",
                         "key_status": "n/a · opencode account", "agentic_tool_enable": True, "tool_calls": True,
                         "high_quality_output": True, "prefer_less_token": True},
                "coding": (ag.get("coding") or {}).get("sdk") or {},
            }
            if not sdk["coding"].get("provider"):
                s, _ = save_sdk("coding")          # seed defaults on first access
                sdk["coding"] = s
            sdk["coding"]["key_status"] = coding_key_status()
            self._json(200, sdk)
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        path = self.path.split("?")[0]
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0)) or 0) or b"{}")
        except Exception:
            body = {}
        if path == "/sdk":
            agent = (body.get("agent") or "").lower()
            if agent != "coding":
                self._json(400, {"error": "model selection applies to agent 'coding'"})
                return
            sdk, err = save_sdk(agent, (body.get("model") or "").strip() or None)
            if err:
                self._json(400, {"error": err})
                return
            self._json(200, sdk)
            return
        if path != "/suggest":
            self._json(404, {"error": "not found"})
            return
        agent = (body.get("agent") or "").lower()
        statement = (body.get("base_statement") or "").strip()
        if agent not in ("plan", "coding"):
            self._json(400, {"error": "agent must be 'plan' or 'coding'"})
            return
        if not statement:
            self._json(400, {"error": "base_statement is required"})
            return
        api_key, _ = key()
        if not api_key:
            self._json(503, {"error": "JEV_API_KEY not set — run.cmd instructions: set JEV_API_KEY first"})
            return
        resp = systemone(api_key, {"agent": agent, "base_statement": statement}, agent_questions(agent))
        saved = save_live(agent, statement, resp)
        self._json(200 if not resp.get("error") else 502, saved)


def main():
    if "--health" in sys.argv:
        api_key, src = key()
        print(json.dumps({"key": "set" if api_key else "missing", "key_source": src, "model": MODEL}))
        return
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"kdwpc-jev: JEV suggestion bridge on http://localhost:{PORT}  (model {MODEL})  Ctrl+C to stop")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nkdwpc-jev: stopped")


if __name__ == "__main__":
    main()