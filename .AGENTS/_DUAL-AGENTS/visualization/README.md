# KD-WPC — Agent Activity Visualization (Dual-Agent Async)

A **KD-WPC**-branded adaptation of **[Agent Activity](https://github.com/angusforbes/omarchy-agent-activity-visualization)** by **Angus Forbes** (MIT) — a local dashboard that charts *what your coding agents actually worked on*, computed **only from your OpenCode session logs** (no cloud, no AI tagging).

On top of the upstream engine we add a **topology panel** that visualises the WPC2 **dual-agent async pipeline**: **ORCHESTRATOR on top**, **AGENT-PLAN (left)** and **AGENT-CODING (right)** below, and a **middle dual-agent comms + JEV box** — with animated connectors that flow while an agent is actually running. It also carries the `GATE → PLAN → SEED 00 → POLICY → CODING → VERIFY` pipeline state and the two handoff seeds.

Upstream is an Omarchy/Quickshell (Linux-only) bar widget. What we vendor is the **portable core** — the collector (`vendor/odv.py`) and the Canvas chart engine (`vendor/charts.js`) — re-rendered as a plain browser page you can run on Windows.

---

## Run it (Windows)

Just double-click **`run.cmd`**, or from a terminal:

```bash
cd .AGENTS/_DUAL-AGENTS/visualization
python kdwpc_collect.py            # ingest OpenCode logs + build snapshot + parse seeds
python -m http.server 8777         # then open http://localhost:8777/kdwpc.html
```

Flags for `kdwpc_collect.py`:

| flag | effect |
| --- | --- |
| *(none)* | ingest + tag + build from your real OpenCode sessions, copy `snapshot.json`, write the orchestrator + live JSON |
| `--reset` | wipe the derived database first, then re-ingest everything |
| `--no-collect` | skip the OpenCode ingest; only refresh the orchestrator + live JSON from the seeds (instant) |
| `--watch N` | **LIVE mode**: keep re-collecting every N seconds until Ctrl+C, so the dashboard tails your agents in real time |

### LIVE mode

Start the collector watching in one window and the server in another, then press **`LIVE`** in the dashboard header:

```bash
python kdwpc_collect.py --watch 30   # refresh every 30 s  (Ctrl+C to stop)
python kdwpc_jev.py                  # JEV suggestion bridge (set JEV_API_KEY first)
python -m http.server 8777
```

…or just double-click **`run.cmd live`** (opens all three windows for you). While LIVE is on the dashboard:

- polls `snapshot.json` + `kdwpc_orchestrator.json` + `kdwpc_live.json` every **20 s** (cache-busted, atomic writes),
- shows a `LIVE · Ns ago · poll ok` ticker (flips to `reconnecting` if a fetch fails — last data is kept),
- auto-tails to the **15M** range,
- animates the topology connectors of every agent that is `running`/`warm`, and paints the agent boxes' status pills (`RUNNING` / `WARM` / `IDLE`) from the live OpenCode database — no page reload needed.

The per-agent live status (`kdwpc_live.json`) is read **read-only** from `opencode.db`'s `session_v2` table (`agent` ∈ `plan`/`build` → Agent-Plan / Agent-Coding), signed by the newest `session_message.time_updated` so a session that is still open keeps appearing as `running`.

### Per-agent JEV integration

Each agent has **its own JEV integration**, read straight from its own ruleset file (both are loaded as project instructions via `.opencode/opencode.jsonc`):

| Agent | JEV role | Where it lives |
| --- | --- | --- |
| **AGENT-PLAN** | **statement generation** — base statements → JEV statements (`CHOICE` / `NOUL` / `SCORE`), `= == ===` equality checks on pre/post-output | `AGENT-PLAN/JEV_RULESET_AGENT-PLAN.md` (+ base statements) |
| **AGENT-CODING** | **quality checks** — `use_jev_for_quality_checks`, browser-capture diff fed into JEV for `post_output` verdicts, seed status back to orchestrator | `AGENT-CODING/JEV_RULESET_AGENT-CODING.md` |

The dashboard surfaces both: each agent box carries a `JEV` row (`LIVE` / `PENDING` pill + the agent's JEV role), and the middle box shows `PLAN` / `CODING` JEV pills side by side with the seed lanes. Both flip to `LIVE` the moment `JEV_API_KEY` is set (kit rule: unset key ⇒ every JEV item is `PENDING_TYPESAFE_API_KEY` — nothing is fabricated).

### JEV suggestion boxes — base_statement → jev_statements

Each agent box (AGENT-PLAN and AGENT-CODING) also has a **`JEV SUGGESTION`** box: a textarea where you type a *base statement*, and a **`Generate → jev_statements`** button. When `JEV_API_KEY` is set, the button asks JEV (Typesafe System One, `POST https://api.typesafe.ai/v1/systemone`) with the agent's own `CHOICE` / `NOUL` / `SCORE` question set (plan: stack / base-change / impact; coding: constraint / coverage / complexity) and shows the generated statements in the box, saved to `kdwpc_live.json` (`agents.<agent>.jev_suggestion`).

Example — AGENT-CODING JEV suggestion input:

```
i want three.js stack to be added for visualisation and can read .excalidraw file and generate the requested drawings from the .excalidraw
```

The key never touches the browser. A tiny local bridge **`kdwpc_jev.py`** (port **8778**, stdlib only) owns it: the dashboard `POST`s the statement to `http://localhost:8778/suggest`, the bridge injects the key, calls System One, and atomically saves the generated statements into `kdwpc_live.json`. Start it with `python kdwpc_jev.py` (or `run.cmd live` starts it for you; `run.cmd jev` starts only the bridge). Status endpoints: `GET /health` shows `key: set|missing`; a missing key returns `503` with a clear hint instead of guessing.

### Per-agent SDK config (current demonstration)

Each agent box has an **`SDK CONFIG`** row showing the real runtime stack (mirrors `services.js` → `services.sdk`):

| Agent | Provider | Model | Key |
| --- | --- | --- | --- |
| **AGENT-PLAN** | `opencode` | `big-pickle` | none (OpenCode account model) |
| **AGENT-CODING** | `openai SDK` · `https://litellm.rapidscreen.io/v1` | **selector**, default `deepseek-v4-flash` | `OPENAI_API_KEY` env-only |

The **model selector** in the AGENT-CODING box offers: `gpt-5.5` · `gpt-5.4` · `gpt-5.4-mini` · `gpt-5.4-nano` · `gpt-5.6-sol` · `gpt-5.6-luna` · `gpt-5.6-terra` · `gpt-6-sol` · `gpt-6-luna` · `deepseek-v4-flash` (default). Picking one saves it through the bridge (`POST /sdk`) into `kdwpc_live.json` → `agents.coding.sdk.model`, where the collector carries it forward; the row also shows the key status (SET / missing, always env-only) and the agentic tooling flags (`agentic_tool_enable`, `tool_calls`, `high_quality_output`, `prefer_less_token`, `token_efficient` + `compactDOM`/`snapDOM`/`html2canvas`/`playwrightOrbrowserOSneo`).

#### Setting the JEV API key (terminal)

The key is read, in order, from `JEV_API_KEY`, `TYPESAFE_API_KEY`, or the odv secret file `~/.pi/agent/secrets/typesafe_api_key`. It must be in the **bridge's** environment, so set it before starting the bridge (or in the `run.cmd live` bridge window):

```bat
rem cmd — current window only
set JEV_API_KEY=sk-your-typesafe-key

rem PowerShell — current window only
$env:JEV_API_KEY="sk-your-typesafe-key"

rem persist for all future windows (then reopen the terminal)
setx JEV_API_KEY sk-your-typesafe-key
```

Then verify: `python kdwpc_jev.py --health` → `{"key": "set", ...}`, and both per-agent JEV pills (plus the middle-box verdicts row) flip to `LIVE`.

---

## What it shows

| Area | Chart | Source |
| --- | --- | --- |
| **Topology** | ORCHESTRATOR (top) → AGENT-PLAN (left) · comms+JEV (middle) · AGENT-CODING (right), animated connectors + live status pills + **per-agent JEV** rows + **SDK CONFIG** rows (model selector for coding) + **JEV SUGGESTION** boxes (base_statement → jev_statements) | `kdwpc_live.json` + seeds |
| KPIs | agent time, your time, prompts, tokens, cost, sessions | snapshot |
| **When** | theme × time heatmap (agent time vs your time) | snapshot |
| **Where the tokens went** | token **Sankey**: tokens → agent → theme → work kind | snapshot |
| **Themes over time** | theme **stream** | snapshot |
| **Topic map** | topic **circle-pack** (deeper fill = rising) | snapshot |
| Terms / Work mix / Agents at once / Tools | rising–fading terms, busy time by kind, concurrency, tool calls | snapshot |
| **Subagents** / **Subagent runs** | runs by type · outcome, and when × how long · by model | OpenCode `task` tool calls + child sessions |

The **Subagents** charts are where the dual-agent orchestration shows up in real data: OpenCode logs every `task` call (`agent-plan`, `agent-coding`, `orchestrator`) as a subagent run.

Hover any chart for details; the `15M / 1H / 6H / 24H / 7D / 1MO` buttons re-render for that range — and in LIVE mode the dashboard tail-locks to 15M.

---

## Files

```
visualization/
  kdwpc.html             KD-WPC dashboard (topology + JEV suggestion boxes + rebranded upstream charts)
  kdwpc_collect.py       wrapper: runs the collector, copies the snapshot, writes orchestrator + live JSON, --watch
  kdwpc_jev.py           JEV suggestion bridge: owns JEV_API_KEY, calls Typesafe System One, writes jev_statements
  run.cmd                Windows one-click: collect -> serve -> open browser
                         (run.cmd live = collector --watch + JEV bridge + server · run.cmd jev = bridge only)
  LICENSE                upstream MIT license (Angus Forbes)
  vendor/
    odv.py               upstream collector (stdlib only), KD-WPC-patched — see below
    charts.js            upstream Canvas 2D chart engine (unchanged)
  data/                  generated — gitignored (snapshot.json, kdwpc_orchestrator.json, kdwpc_live.json)
```

---

## KD-WPC changes vs upstream

`vendor/odv.py` — all changes are Windows/data-format robustness, semantics unchanged:

1. **Windows privacy gate.** Upstream fails closed on Windows (`os.getuid()` / `chmod 0o700` are POSIX-only). Guarded behind `os.name == "nt"`.
2. **`%-m/%-d` strftime.** POSIX-only format specifier crashed `build` on Windows (`ValueError`). Replaced with a portable month/day string.
3. **Structured tool queries.** `call_of()` assumed `query` was a string; real OpenCode logs contain calls whose `query` is a **dict** (e.g. `cloudflare-observability_query_worker_observability`), which crashed ingest with `KeyError: slice(None, 160, None)`. Non-string queries are now safely serialised.
4. **New OpenCode schema (`session_v2` / `session_message`).** Newer OpenCode moved sessions out of `session`/`message`/`part` into `session_v2` + `session_message`. Upstream only reads the old tables, so on this machine it silently stopped at the schema upgrade and saw **nothing after Sep 26**. The collector now reads both schemas, maps the v2 message `content` parts and part-level `time` to the upstream shape, and uses the v2 `session.agent` field (`plan` / `build` / `orchestrator`) for subagent-type labels.
5. **`KDWPC_DATA` env override** for the derived data directory (defaults to `~/.local/share/kdwpc-agent-activity`).

`kdwpc.html` / `kdwpc_collect.py` — new: the topology panel (live per-agent boxes + connectors), the orchestrator summary, the collector wrapper, and the browser layout. `charts.js` is untouched.

---

## Data & privacy

- **Real local data.** The collector reads your OpenCode store (`~/.local/share/opencode` — override with `OPENCODE_DATA_DIR`) **read-only**; it never modifies OpenCode's database.
- Derived data (a small SQLite DB + snapshot) lives in `~/.local/share/kdwpc-agent-activity/` and `visualization/data/`. The latter is **gitignored**, so nothing derived is committed.
- Tagging uses **rules only** (`jev: false`) — no AI calls on the charts. JEV is used **only** when you type a base statement into a JEV SUGGESTION box and the key is set: the local bridge (`kdwpc_jev.py`, port 8778) sends that one statement + its question set to `api.typesafe.ai/v1/systemone`, and saves the answers locally. The key is env-only, never committed, never sent to the browser, never echoed in responses (upstream error text is truncated and key-redacted).

---

## Forks & sandboxing

**Forks are snapshots, not mirrors.** GitHub makes a full copy of the repo at the moment someone forks it — your later changes never touch an existing fork, and a fork owner only ever sees them if they deliberately sync from upstream. So nothing you commit after a fork happened can affect that fork. The one thing that *can* affect anyone is what's on `main` **right now** (that's what new forks clone), which is why this kit keeps `main` clean:

- **no secrets** — the JEV key is env-only (`JEV_API_KEY` → `TYPESAFE_API_KEY` → `~/.pi/agent/secrets/typesafe_api_key`); `.env*` is gitignored, and nothing key-like ships in tracked files,
- **no derived data** — `visualization/data/` and `__pycache__/` are gitignored; derived DBs live in `~/.local/share/kdwpc-agent-activity/`,
- **no writes to your OpenCode store** — the collector opens `opencode.db` read-only (`file:...?mode=ro`) and only writes to its own data dirs.

Optional hardening on GitHub's side: enable **branch protection on `main`** (Settings → Branches → require a pull request review) so nothing is merged without a review — with direct pushes to `main` blocked, the canonical branch only changes through deliberate, reviewed PRs.

**Clean-room run without a VM.** Use the collector's two env overrides from a **scratch clone**, so the empty-store run never touches your real checkout's `data/` or your live OpenCode store:

```bat
git clone https://github.com/ctaxnagomi/wpc2-dual-agent C:\tmp\forktest\repo
mkdir C:\tmp\forktest\opencode C:\tmp\forktest\data
cd C:\tmp\forktest\repo\.AGENTS\_DUAL-AGENTS\visualization
set OPENCODE_DATA_DIR=C:\tmp\forktest\opencode
set KDWPC_DATA=C:\tmp\forktest\data
python kdwpc_collect.py
python -m http.server 8777
```

An explicit `OPENCODE_DATA_DIR` **fails closed**: an empty (or copied) dir is the *only* store the collector reads — it never falls back to `~/.local/share/opencode`, so your real session logs are never touched. Empty store → no agents and empty charts (exactly what a fork user sees); point the override at a **copy** of your OpenCode store to reproduce your real data in isolation (read-only either way). Note: the live JSON / snapshot are derived and gitignored, so a clean-room run from your *real* checkout would reset the live dashboard until you re-run the collector without the overrides.

---

## Attribution & license

Charts, collector, and the dashboard concept are by **Angus Forbes** — MIT, see [`LICENSE`](./LICENSE). The KD-WPC adaptation (orchestrator panel, collector wrapper, Windows/data fixes) is part of the `wpc2-dual-agent` kit.

Upstream project: <https://github.com/angusforbes/omarchy-agent-activity-visualization>
