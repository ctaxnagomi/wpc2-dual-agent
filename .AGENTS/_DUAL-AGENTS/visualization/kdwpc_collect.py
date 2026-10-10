#!/usr/bin/env python3
"""KD-WPC collector — build the dual-agent activity dashboard from REAL OpenCode session logs.

Wraps the vendored Omarchy "Agent Activity" collector (vendor/odv.py — MIT, (c) Angus Forbes) and
adds a KD-WPC layer: an orchestrator / dual-agent pipeline derived from the handoff seeds.

What it does
  1. runs the vendored collector (`odv.py run`) against your OpenCode data    -> <data>/snapshot.json
  2. copies that snapshot next to the dashboard                               -> data/snapshot.json
  3. parses the two seeds and writes the async pipeline state                 -> data/kdwpc_orchestrator.json

Usage
  python kdwpc_collect.py              # ingest + tag + build everything
  python kdwpc_collect.py --reset      # wipe the derived database first
  python kdwpc_collect.py --no-collect # only refresh the orchestrator json (fast, no OpenCode ingest)
  python kdwpc_collect.py --watch 30   # LIVE: re-collect every 30s (Ctrl+C to stop)

Then serve the folder and open the dashboard:
  python -m http.server 8777           ->  http://localhost:8777/kdwpc.html
(or just run run.cmd on Windows; `run.cmd live` starts collector+server together)
"""
import argparse
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.realpath(__file__))          # .../_DUAL-AGENTS/visualization
VENDOR = os.path.join(HERE, "vendor", "odv.py")
DATA_DEST = os.path.join(HERE, "data")
SEED_DIR = os.path.normpath(os.path.join(HERE, "..", "seeds"))
SEED_PLAN = os.path.join(SEED_DIR, "00_seed_plan_to_coding.md")
SEED_CODE = os.path.join(SEED_DIR, "01_seed_coding_to_plan.md")

# Derived data (DB + snapshot) is kept OUT of the repo.
USER_DATA = os.environ.get("KDWPC_DATA") or os.path.join(
    os.path.expanduser("~"), ".local", "share", "kdwpc-agent-activity"
)

LIVE_JSON = os.path.join(DATA_DEST, "kdwpc_live.json")
LIVE_RUNNING = 120      # s: a message within this window  -> agent "running" in the topology
LIVE_WARM = 1800        # s: within this window            -> "warm" (recent activity)


def find_opencode_db():
    """Locate the live OpenCode database (read-only source for the topology).

    Fails CLOSED: if OPENCODE_DATA_DIR is explicitly set but contains no opencode.db,
    return None (idle topology) instead of silently falling back to the real store —
    an override that points nowhere must never read the user's live sessions.
    """
    cands = []
    env = os.environ.get("OPENCODE_DATA_DIR")
    if env:
        cands.append(os.path.join(env, "opencode.db"))
        if not any(os.path.isfile(c) for c in cands):
            return None
    cands.append(os.path.join(os.path.expanduser("~"), ".local", "share", "opencode", "opencode.db"))
    for c in cands:
        if os.path.isfile(c):
            return c
    return None


def read_live(seed0, seed1):
    """Live topology state: per-agent (plan/build) status from opencode.db + JEV mode + gate.

    Runs against the live OpenCode database read-only. Plan/coding status comes from the
    newest session_v2 row for each agent, signed by the newest session_message time_updated
    (session_v2.time_updated lags while a session is still open).
    """
    now = time.time()
    state = {
        "generated": int(now),
        "jev_mode": "LIVE" if os.environ.get("JEV_API_KEY") else "STUB",
        "jev_status": None if os.environ.get("JEV_API_KEY") else "PENDING_TYPESAFE_API_KEY",
        "agents": {
            "plan":   {"id": "agent-plan",   "label": "AGENT-PLAN",   "status": "idle", "task": None, "model": None,
                       "msgs": 0, "tokens_out": 0, "session": None, "last": None, "age": None},
            "coding": {"id": "agent-coding", "label": "AGENT-CODING", "status": "idle", "task": None, "model": None,
                       "msgs": 0, "tokens_out": 0, "session": None, "last": None, "age": None},
        },
        "orchestrator": {
            "label": "ORCHESTRATOR",
            "policy": "async gated routing · plan→coding→plan (JEV-ruleset)",
            "seeds": {},
        },
    }
    # orchestrator gate follows the handoff seeds
    ap = (seed0 or {}).get("approved_stack")
    s0 = (seed0 or {}).get("status", "MISSING")
    s1 = (seed1 or {}).get("status", "MISSING")
    state["orchestrator"]["seeds"] = {
        "00_plan_to_coding": s0, "01_coding_to_plan": s1,
        "gate": "OPEN" if (ap and s0 == "APPROVED") else ("SEEDED" if ap or s0 != "MISSING" else "WAITING"),
    }
    db = find_opencode_db()
    if not db:
        return state
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=5)
        con.execute("PRAGMA query_only=1")
        rows = con.execute("""
            SELECT s.agent, s.id, s.title, s.model,
                   (SELECT MAX(sm.time_updated) FROM session_message sm WHERE sm.session_id = s.id),
                   (SELECT COUNT(*) FROM session_message sm WHERE sm.session_id = s.id),
                   s.tokens_output
            FROM session_v2 s WHERE s.agent IN ('plan','build')""").fetchall()
        con.close()
    except sqlite3.Error as e:
        print(f"kdwpc: live opencode read failed: {e}", file=sys.stderr)
        return state
    best = {}
    for agent, sid, title, model, last, msgs, tok in rows:
        if best.get(agent, (0,))[0] >= (last or 0):
            continue
        best[agent] = (last or 0, sid, title, model, msgs or 0, tok or 0)
    map_agent = {"plan": "plan", "build": "coding"}
    for agent, (last, sid, title, model, msgs, tok) in best.items():
        key = map_agent.get(agent)
        if not key:
            continue
        age = (now - last / 1000) if last else None
        status = "running" if age is not None and age <= LIVE_RUNNING else ("warm" if age is not None and age <= LIVE_WARM else "idle")
        mid = None
        if model:
            try:
                mid = (json.loads(model) or {}).get("id")
            except Exception:
                mid = model
        a = state["agents"][key]
        a.update(status=status, task=title, model=mid, msgs=msgs, tokens_out=tok,
                 session=sid, last=last, age=round(age) if age is not None else None)
    # each agent carries its OWN JEV integration (from its own ruleset)
    for key, path in JEVRULES.items():
        r = read_agent_ruleset(path)
        state["agents"][key]["jev"] = {
            "role": JEV_ROLE.get(key, "JEV"),
            "ruleset": os.path.basename(path),
            "loaded": bool(r),
            # kit rule: JEV is env-only — unset JEV_API_KEY => every JEV item is PENDING_TYPESAFE_API_KEY
            "status": "LIVE" if os.environ.get("JEV_API_KEY") else "PENDING_TYPESAFE_API_KEY",
            "declared": (r or {}).get("status"),
            "flags": (r or {}).get("flags", []),
        }
    # carry over any jev_suggestion / sdk the local bridge (kdwpc_jev.py) generated since the last pass
    try:
        prev = {}
        if os.path.isfile(LIVE_JSON):
            prev = json.load(open(LIVE_JSON, encoding="utf-8")) or {}
        pag = prev.get("agents") or {}
        for k in state["agents"]:
            sug = (pag.get(k) or {}).get("jev_suggestion")
            if sug:
                state["agents"][k]["jev_suggestion"] = sug
            # per-agent SDK config (current demonstration): defaults + any picked model
            conf = dict(SDK_CONF.get(k, {}))
            if conf:
                old = (pag.get(k) or {}).get("sdk") or {}
                if k == "coding":
                    pick = (old.get("model") or conf["model"])
                    if pick not in conf["models"]:
                        pick = conf["model"]
                    conf["model"] = pick
                    conf["key_status"] = "SET · env-only (OPENAI_API_KEY)" if os.environ.get("OPENAI_API_KEY") \
                        else "missing · env-only (OPENAI_API_KEY)"
                state["agents"][k]["sdk"] = conf
    except Exception as e:
        print(f"kdwpc: jev_suggestion/sdk carry-over failed: {e}", file=sys.stderr)
    return state


def find_project_root():
    w = HERE
    for _ in range(8):
        if os.path.isdir(os.path.join(w, ".AGENTS")):
            return w
        nxt = os.path.dirname(w)
        if nxt == w:
            break
        w = nxt
    return os.path.dirname(SEED_DIR)


PROJECT_ROOT = find_project_root()

# Per-agent JEV integration, straight from each agent's own ruleset file.
JEVRULES = {
    "plan":   os.path.join(PROJECT_ROOT, ".AGENTS", "_DUAL-AGENTS", "AGENT-PLAN", "JEV_RULESET_AGENT-PLAN.md"),
    "coding": os.path.join(PROJECT_ROOT, ".AGENTS", "_DUAL-AGENTS", "AGENT-CODING", "JEV_RULESET_AGENT-CODING.md"),
}
JEV_ROLE = {
    "plan":   "statement gen: base statements -> CHOICE / NOUL / SCORE",
    "coding": "quality checks: browser-capture diff -> verdicts (post_output)",
}

# Per-agent SDK config — mirror of services.js `services.sdk` (keep in sync).
CODING_MODELS = ["gpt-5.5", "gpt-5.4", "gpt-5.4-mini", "gpt-5.4-nano",
                 "gpt-5.6-sol", "gpt-5.6-luna", "gpt-5.6-terra",
                 "gpt-6-sol", "gpt-6-luna", "deepseek-v4-flash"]
SDK_CONF = {
    "plan": {
        "provider": "opencode",
        "model": "big-pickle",
        "base_url": None,
        "key_env": None,
        "key_status": "n/a · opencode account",
        "agentic_tool_enable": True, "tool_calls": True, "high_quality_output": True, "prefer_less_token": True,
    },
    "coding": {
        "provider": "openai SDK",
        "model": "deepseek-v4-flash",             # default; dashboard selector / bridge may change it
        "base_url": "https://litellm.rapidscreen.io/v1",
        "key_env": "OPENAI_API_KEY",
        "models": list(CODING_MODELS),
        "agentic_tool_enable": True, "tool_calls": True, "high_quality_output": True,
        "prefer_less_token": True, "token_efficient": True,
        "imports": ["compactDOM", "snapDOM", "html2canvas", "playwrightOrbrowserOSneo"],
    },
}


def read_agent_ruleset(path):
    """Pull the JEV integration facts out of one agent's ruleset (tolerantly)."""
    if not os.path.isfile(path):
        return None
    txt = open(path, "r", encoding="utf-8").read()
    out = {
        "loaded": True,
        "status": "PENDING_TYPESAFE_API_KEY" if "PENDING_TYPESAFE_API_KEY" in txt else None,
        "flags": [],
    }
    for flag in ("use_jev_for_quality_checks", "run_quality_check_via_jev", "seed_status_to_orchestrator",
                 "apply_equality_rules", "agentic_tool_enable", "confirm_stack_matches_approved"):
        if re.search(r"\b" + re.escape(flag) + r"\b", txt):
            out["flags"].append(flag)
    return out


def ensure_config():
    """Create the collector config once: recognise the folders around this project as projects."""
    os.makedirs(USER_DATA, exist_ok=True)
    cfg_path = os.path.join(USER_DATA, "config.json")
    if os.path.exists(cfg_path):
        return
    parent = os.path.dirname(PROJECT_ROOT) or PROJECT_ROOT
    cfg = {
        "maxRange": "1mo",
        "projectRoots": [parent],
        "sources": {},
    }
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def run_collector(reset=False):
    env = dict(os.environ)
    env["KDWPC_DATA"] = USER_DATA
    cmd = [sys.executable, VENDOR]
    if reset:
        subprocess.run(cmd + ["reset"], env=env, check=False)
    return subprocess.run(cmd + ["run"], env=env).returncode


def copy_snapshot():
    os.makedirs(DATA_DEST, exist_ok=True)
    src = os.path.join(USER_DATA, "snapshot.json")
    if os.path.isfile(src):
        tmp = os.path.join(DATA_DEST, "snapshot.json.tmp")
        shutil.copyfile(src, tmp)
        os.replace(tmp, os.path.join(DATA_DEST, "snapshot.json"))   # atomic: a live dashboard never reads a half-written file
        return True
    return False


def parse_seed(path):
    """Extract the ```json fenced block from a seed markdown file."""
    if not os.path.isfile(path):
        return None
    txt = open(path, "r", encoding="utf-8").read()
    m = re.search(r"```json\s*(\{.*?\})\s*```", txt, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None


def pipeline_state(seed0, seed1):
    approved = (seed0 or {}).get("approved_stack")
    src = (seed0 or {}).get("source_visual")
    s0 = (seed0 or {}).get("status", "MISSING")
    s1 = (seed1 or {}).get("status", "MISSING")
    arts = ((seed1 or {}).get("build") or {}).get("artifacts") or []

    def done(ok):
        return "done" if ok else "pending"

    return [
        {"step": "gate",   "label": "GATE",     "state": done(bool(approved) and bool(src)), "note": "approved stack + viewports"},
        {"step": "plan",   "label": "PLAN",     "state": done(bool(src)),                    "note": "parse .excalidraw to visual_outline"},
        {"step": "seed",   "label": "SEED 00",  "state": done(bool(src) and bool(approved)), "note": "PLAN to CODING handoff"},
        {"step": "policy", "label": "POLICY",   "state": done(s0 == "APPROVED"),             "note": "gate the seed"},
        {"step": "build",  "label": "CODING",   "state": done(bool(arts)),                   "note": "implement from seed"},
        {"step": "verify", "label": "VERIFY",   "state": done(s1 in ("DONE", "VERIFIED")),   "note": "checks + status seed"},
    ]


def write_orchestrator(seed0, seed1):
    os.makedirs(DATA_DEST, exist_ok=True)
    project = (seed0 or {}).get("project") or (seed1 or {}).get("project") or "WPC2_Zero_Prompts_Demo"
    out = {
        "generated": int(time.time()),
        "project": project,
        "pipeline": pipeline_state(seed0, seed1),
        "seeds": {"plan_to_coding": seed0, "coding_to_plan": seed1},
        "agents": [
            {"id": "orchestrator", "name": "ORCHESTRATOR", "role": "async gated routing / policy gate"},
            {"id": "agent-plan",   "name": "AGENT-PLAN",   "role": "visual intake to seed"},
            {"id": "agent-coding", "name": "AGENT-CODING", "role": "build from seed"},
        ],
    }
    dest = os.path.join(DATA_DEST, "kdwpc_orchestrator.json")
    tmp = dest + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    os.replace(tmp, dest)                                # atomic write, for live polling
    return out


def write_live(seed0, seed1):
    """Refresh data/kdwpc_live.json (topology) atomically so a live dashboard never reads a half-file."""
    os.makedirs(DATA_DEST, exist_ok=True)
    out = read_live(seed0, seed1)
    tmp = LIVE_JSON + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    os.replace(tmp, LIVE_JSON)
    return out


def collect_cycle(reset=False):
    """One full pass: ingest -> snapshot -> orchestrator json -> live json. Returns True when snapshot landed."""
    if run_collector(reset) != 0:
        print("kdwpc: collector returned non-zero; continuing with the seed layer", file=sys.stderr)
    ok = copy_snapshot()
    if ok:
        print(f"kdwpc: copied snapshot to {os.path.join(DATA_DEST, 'snapshot.json')}")
    else:
        print("kdwpc: no snapshot produced (no OpenCode sessions found?)", file=sys.stderr)
    return ok


def main():
    ap = argparse.ArgumentParser(prog="kdwpc_collect")
    ap.add_argument("--reset", action="store_true", help="wipe the derived database first")
    ap.add_argument("--no-collect", action="store_true", help="skip the OpenCode ingest; only refresh the orchestrator + live json")
    ap.add_argument("--watch", type=float, metavar="N", help="LIVE: re-collect every N seconds (Ctrl+C to stop)")
    a = ap.parse_args()

    print(f"kdwpc: data dir  {USER_DATA}")
    print(f"kdwpc: project   {PROJECT_ROOT}")
    ensure_config()

    def one_pass():
        if not a.no_collect:
            collect_cycle()
        seed0, seed1 = parse_seed(SEED_PLAN), parse_seed(SEED_CODE)
        write_orchestrator(seed0, seed1)
        lv = write_live(seed0, seed1)
        ag = " | ".join(f"{k}: {v['status']}" for k, v in lv["agents"].items())
        print(f"kdwpc: live [{ag}] jev {lv['jev_mode']} gate {lv['orchestrator']['seeds'].get('gate')}")

    one_pass()
    if a.watch:
        print(f"kdwpc: watching every {a.watch:g}s - open http://localhost:8777/kdwpc.html and press LIVE  (Ctrl+C to stop)")
        try:
            while True:
                time.sleep(max(5.0, a.watch))
                one_pass()
        except KeyboardInterrupt:
            print("\nkdwpc: watch stopped")
        return

    print(f"kdwpc: wrote {os.path.join(DATA_DEST, 'kdwpc_orchestrator.json')}")
    print("kdwpc: serve with  ->  python -m http.server 8777   then open  http://localhost:8777/kdwpc.html")


if __name__ == "__main__":
    main()
