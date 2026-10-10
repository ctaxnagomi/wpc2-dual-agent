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

Then serve the folder and open the dashboard:
  python -m http.server 8777           ->  http://localhost:8777/kdwpc.html
(or just run run.cmd on Windows)
"""
import argparse
import json
import os
import re
import shutil
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
        shutil.copyfile(src, os.path.join(DATA_DEST, "snapshot.json"))
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
    with open(os.path.join(DATA_DEST, "kdwpc_orchestrator.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    return out


def main():
    ap = argparse.ArgumentParser(prog="kdwpc_collect")
    ap.add_argument("--reset", action="store_true", help="wipe the derived database first")
    ap.add_argument("--no-collect", action="store_true", help="skip the OpenCode ingest; only refresh the orchestrator json")
    a = ap.parse_args()

    print(f"kdwpc: data dir  {USER_DATA}")
    print(f"kdwpc: project   {PROJECT_ROOT}")
    ensure_config()

    if not a.no_collect:
        if run_collector(a.reset) != 0:
            print("kdwpc: collector returned non-zero; continuing with the seed layer", file=sys.stderr)
        if copy_snapshot():
            print(f"kdwpc: copied snapshot to {os.path.join(DATA_DEST, 'snapshot.json')}")
        else:
            print("kdwpc: no snapshot produced (no OpenCode sessions found?)", file=sys.stderr)

    seed0 = parse_seed(SEED_PLAN)
    seed1 = parse_seed(SEED_CODE)
    write_orchestrator(seed0, seed1)

    print(f"kdwpc: wrote {os.path.join(DATA_DEST, 'kdwpc_orchestrator.json')}")
    print("kdwpc: serve with  ->  python -m http.server 8777   then open  http://localhost:8777/kdwpc.html")


if __name__ == "__main__":
    main()
