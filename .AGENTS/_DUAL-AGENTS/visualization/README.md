# KD-WPC — Agent Activity Visualization (Dual-Agent Async)

A **KD-WPC**-branded adaptation of **[Agent Activity](https://github.com/angusforbes/omarchy-agent-activity-visualization)** by **Angus Forbes** (MIT) — a local dashboard that charts *what your coding agents actually worked on*, computed **only from your OpenCode session logs** (no cloud, no AI tagging).

On top of the upstream engine we add a **dual-screen WPC2 demo**, served from **two localhosts**:

- **`http://localhost:8777/kdwpc.html` — LOOP BOARD** — a redesigned **industrial-brutalist topology visualizer**: **ORCHESTRATOR on top**, **AGENT-PLAN (left)** and **AGENT-CODING (right)** below, and a middle **comms + JEV** box. Connector lanes have a **gap in the middle** (a synapse node), and a bright **activity dot travels each lane only while that agent is actually running** (real OpenCode status: `RUNNING` / `WARM` / `IDLE`). It also carries the `GATE → PLAN → SEED 00 → POLICY → CODING → VERIFY` pipeline state and the two handoff seeds.
- **`http://localhost:8779/output.html` — DEMONSTRATION OUTPUT** — the *readouts*: the **JEV SUGGESTION** boxes (base_statement → jev_statements), the **SDK CONFIG** row + **model selector** for Agent-Coding, and the full **activity charts** (what the agents worked on). The demonstrations outputs deliberately live on their **own localhost**, not on the board.

Upstream is an Omarchy/Quickshell (Linux-only) bar widget. What we vendor is the **portable core** — the collector (`vendor/odv.py`) and the Canvas chart engine (`vendor/charts.js`) — re-rendered as a plain browser page you can run on Windows.

---

## Run it (Windows)

Just double-click **`run.cmd`**, or from a terminal:

```bash
cd .AGENTS/_DUAL-AGENTS/visualization
python kdwpc_collect.py            # ingest OpenCode logs + build snapshot + parse seeds
python -m http.server 8777         # then open http://localhost:8777/kdwpc.html   (loop board)
python -m http.server 8779         # then open http://localhost:8779/output.html  (demonstration output)
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
python -m http.server 8777           # loop board
python -m http.server 8779           # demonstration output
```

…or just double-click **`run.cmd live`** (opens all four windows + both pages for you). While LIVE is on either page:

- pools `snapshot.json` + `kdwpc_orchestrator.json` + `kdwpc_live.json` every **20 s** (cache-busted, atomic writes),
- shows a `LIVE · Ns ago · poll ok` ticker (flips to `reconnecting` if a fetch fails — last data is kept),
- auto-tails to the **15M** range,
- on the **board** (8777): animates the connector lanes of every agent that is `running`/`warm` — the lane gap synapse lights, the dash-flow glows and the **activity dot travels** from Orchestrator → agent — and paints the status pills (`RUNNING` / `WARM` / `IDLE`) from the live OpenCode database — no page reload needed.

The per-agent live status (`kdwpc_live.json`) is read **read-only** from `opencode.db`'s `session_v2` table (`agent` ∈ `plan`/`build` → Agent-Plan / Agent-Coding), signed by the newest `session_message.time_updated` so a session that is still open keeps appearing as `running`.

### Per-agent JEV integration

Each agent has **its own JEV integration**, read straight from its own ruleset file (both are loaded as project instructions via `.opencode/opencode.jsonc`):

| Agent | JEV role | Where it lives |
| --- | --- | --- |
| **AGENT-PLAN** | **statement generation** — base statements → JEV statements (`CHOICE` / `NOUL` / `SCORE`), `= == ===` equality checks on pre/post-output | `AGENT-PLAN/JEV_RULESET_AGENT-PLAN.md` (+ base statements) |
| **AGENT-CODING** | **quality checks** — `use_jev_for_quality_checks`, browser-capture diff fed into JEV for `post_output` verdicts, seed status back to orchestrator | `AGENT-CODING/JEV_RULESET_AGENT-CODING.md` |

The screens surface both: each **board** agent box carries a compact `JEV` pill (`LIVE` / `PENDING`), and the middle box shows `PLAN` / `CODING` JEV pills side by side with the seed lanes. Both flip to `LIVE` the moment `JEV_API_KEY` is set (kit rule: unset key ⇒ every JEV item is `PENDING_TYPESAFE_API_KEY` — nothing is fabricated). The full JEV role text and the suggestion boxes live on the **output page**.

### JEV suggestion boxes — base_statement → jev_statements (output page, 8779)

The **demonstration output page** (`http://localhost:8779/output.html`) has a **`JEV SUGGESTION`** box per agent (AGENT-PLAN and AGENT-CODING): a textarea where you type a *base statement*, and a **`Generate → jev_statements`** button. When `JEV_API_KEY` is set, the button asks JEV (Typesafe System One, `POST https://api.typesafe.ai/v1/systemone`) with the agent's own `CHOICE` / `NOUL` / `SCORE` question set (plan: stack / base-change / impact; coding: constraint / coverage / complexity) and shows the generated statements, saved to `kdwpc_live.json` (`agents.<agent>.jev_suggestion`).

### Thought chain (CoT) — what each agent is doing, and what it says to the other

Under each agent's JEV box the output page renders a live **THOUGHT CHAIN**: a chain-of-thought stage strip plus an event log, both built **only from real state** (status, task, msgs, seeds, JEV status — never fabricated lines):

- **Stages** per agent mirror its pipeline and are gated on real facts:
  *AGENT-PLAN:* `READ base statements` → `CHECK equality = == ===` → `THINK task` → `SEED 00` → `MSG → AGENT-CODING`.
  *AGENT-CODING:* `RECV seed 00` → `PARSE .excalidraw` → `BUILD artifacts` → `JEV quality check` → `MSG ← AGENT-PLAN`.
  A stage flips to *done* only when the collector's data confirms it; the stage the agent is **on right now** gets the pulsing cursor (idle ⟹ no cursor).
- **Trigger lamp + box highlight** — the orange lamp in the panel header lights (and the whole JEV box flashes + glows) whenever a **base statement fires**, i.e. `base_statements_stacks.md` / `base_statements_viewports.md` changes (`kdwpc_collect.py` stamps each file's mtime + first content line into `agents.plan.base_statements`), or when a **JEV generation** lands from the bridge. The `ctx ·` chip names exactly *which file/statement the JEV refers to*.
- **Communication events** — seed handoffs appear as directional messages in the chain, so you see what the agent communicated and when: `seed 00 → AGENT-CODING · status … · stack … · visual … · tasks n` and `seed 01 → AGENT-PLAN · artifacts n · stack …` (plus the receive-sides on the partner's chain). The thought line for a trigger echoes the demo format: *“Well based on our compliance of base_statements · stacks i think we should use HTML5 for this case, what do you think Agent-Coding?”* — with the stack filled from `approved_stack` (or `(keep current stack)` until one is approved).
- **Minified JEV verdicts** — under each chain, compact chips for `{choice}` `{noul}` `{score}` from the generated `jev_statements` (with confidence %), plus a `{decision}` chip (filled when the JEV answer carries one, otherwise `— pending JEV key`).

Example — AGENT-CODING JEV suggestion input:

```
i want three.js stack to be added for visualisation and can read .excalidraw file and generate the requested drawings from the .excalidraw
```

The key never touches the browser. A tiny local bridge **`kdwpc_jev.py`** (port **8778**, stdlib only) owns it: the output page `POST`s the statement to `http://localhost:8778/suggest`, the bridge injects the key, calls System One, and atomically saves the generated statements into `kdwpc_live.json`. Start it with `python kdwpc_jev.py` (or `run.cmd live` starts it for you; `run.cmd jev` starts only the bridge). Status endpoints: `GET /health` shows `key: set|missing`; a missing key returns `503` with a clear hint instead of guessing. Both pages show the bridge state in their header gate bar.

### Per-agent SDK config (current demonstration)

The **output page** (8779) carries an **`SDK CONFIG`** table per agent showing the real runtime stack (mirrors `services.js` → `services.sdk`):

| Agent | Provider | Model | Key |
| --- | --- | --- | --- |
| **AGENT-PLAN** | `opencode` | `big-pickle` | none (OpenCode account model) |
| **AGENT-CODING** | `openai SDK` · `https://litellm.rapidscreen.io/v1` | **selector**, default `deepseek-v4-flash` | `OPENAI_API_KEY` env-only |

The **model selector** in the AGENT-CODING panel offers: `gpt-5.5` · `gpt-5.4` · `gpt-5.4-mini` · `gpt-5.4-nano` · `gpt-5.6-sol` · `gpt-5.6-luna` · `gpt-5.6-terra` · `gpt-6-sol` · `gpt-6-luna` · `deepseek-v4-flash` (default). Picking one saves it through the bridge (`POST /sdk`) into `kdwpc_live.json` → `agents.coding.sdk.model`, where the collector carries it forward; the table also shows the key status (SET / missing, always env-only) and the agentic tooling flags (`agentic_tool_enable`, `tool_calls`, `high_quality_output`, `prefer_less_token`, `token_efficient` + `compactDOM`/`snapDOM`/`html2canvas`/`playwrightOrbrowserOSneo`).

**Stack gate (base-statements + JEV compliance).** The AGENT-CODING SDK config may *only* use stacks sourced from `AGENT-PLAN/base_statements_stacks.md` (the organic source of truth: `default_stack` → `HTML5 + SCSS3 + Vanilla JS`, `user_override`, `approved_stack`). `kdwpc_collect.py` parses that file each pass and sets `agents.coding.sdk.stack_allowed` (the only permitted options), `agents.coding.sdk.stack` (approved stack, else the base default — never an arbitrary stack), `stack_source`, `jev_stack_decision` (from the plan agent's JEV `stack_choice` answer), and `stack_compliant` — one of:
`COMPLIANT · approved by JEV` · `COMPLIANT · matches JEV decision` · `NON-COMPLIANT · JEV decided "<other>"` · `pending JEV compliance · verify via Generate` (JEV key not yet set) · `pending · base default (…)`. The bridge's `POST /sdk` mutates the SDK dict in place, so these fields survive model saves; the output page renders them under **stack / stack allowed / jev decision** in the CODING table.

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
| **Board** (8777) | ORCHESTRATOR (top) → AGENT-PLAN (left) · comms+JEV (middle) · AGENT-CODING (right), industrial-brutalist board, connectors with a **gap + synapse** per lane, **activity dots** that travel only while an agent runs, status pills + lamps + scanlines, JEV mini-pills | `kdwpc_live.json` + seeds |
| **Output** (8779) | DEMONSTRATION OUTPUT: per-agent **THOUGHT CHAIN** (CoT stages + trigger lamp + PLAN↔CODING communication events) + **minified {choice} {noul} {score} {decision} chips**, JEV SUGGESTION boxes (base_statement → jev_statements), SDK CONFIG (model selector + key status + tooling), JEV/sdk/bridge status, plus all activity charts below | `kdwpc_live.json` + snapshot + seeds |
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
  kdwpc.html             KD-WPC LOOP BOARD (8777) — industrial-brutalist topology visualizer:
                         gapped connector lanes + activity dots + status pills (topology only)
  output.html            KD-WPC DEMONSTRATION OUTPUT (8779) — JEV suggestion boxes, SDK config
                         (model selector), bridge status + rebranded upstream charts
  kdwpc_collect.py       wrapper: runs the collector, copies the snapshot, writes orchestrator + live JSON, --watch
  kdwpc_jev.py           JEV suggestion bridge: owns JEV_API_KEY, calls Typesafe System One, writes jev_statements
  run.cmd                Windows one-click: collect -> serve 8777 + 8779 -> open both pages
                         (run.cmd live = collector --watch + JEV bridge + both servers · run.cmd jev = bridge only)
  LICENSE                upstream MIT license (Angus Forbes)
  vendor/
    odv.py               upstream collector (stdlib only), KD-WPC-patched — see below
    charts.js            upstream Canvas 2D chart engine (unchanged, palette-driven — output page passes a dark palette)
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

`kdwpc.html` (board) / `output.html` (demonstration output) / `kdwpc_collect.py` — new: the topology board (live per-agent boxes + gapped connector lanes with travel dots), the orchestrator summary, the collector wrapper, and the browser layout. The board was redesigned as an **industrial-brutalist** control-room UI (dark palette, mono type, hazard strips, LED lamps, corner ticks) with **design-motion principles**: expo-out staggered reveals, transform/opacity-only animation, isochronic dash-flow, a single `requestAnimationFrame` loop for the travel dots, and a `prefers-reduced-motion` fallback that renders the static final state. `charts.js` is untouched.

---

## Data & privacy

- **Real local data.** The collector reads your OpenCode store (`~/.local/share/opencode` — override with `OPENCODE_DATA_DIR`) **read-only**; it never modifies OpenCode's database.
- Derived data (a small SQLite DB + snapshot) lives in `~/.local/share/kdwpc-agent-activity/` and `visualization/data/`. The latter is **gitignored**, so nothing derived is committed.
- Tagging uses **rules only** (`jev: false`) — no AI calls on the charts. JEV is used **only** when you type a base statement into a JEV SUGGESTION box (output page, 8779) and the key is set: the local bridge (`kdwpc_jev.py`, port 8778) sends that one statement + its question set to `api.typesafe.ai/v1/systemone`, and saves the answers locally. The key(s) (`JEV_API_KEY`, `OPENAI_API_KEY`) are env-only, never committed, never sent to the browser, never echoed in responses (upstream error text is truncated and key-redacted).

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
