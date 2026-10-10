# KD-WPC — Agent Activity Visualization (Dual-Agent Async)

A **KD-WPC**-branded adaptation of **[Agent Activity](https://github.com/angusforbes/omarchy-agent-activity-visualization)** by **Angus Forbes** (MIT) — a local dashboard that charts *what your coding agents actually worked on*, computed **only from your OpenCode session logs** (no cloud, no AI tagging).

On top of the upstream engine we add an **ORCHESTRATOR panel** that visualises the WPC2 **dual-agent async pipeline**: `GATE → PLAN → SEED 00 → POLICY → CODING → VERIFY`, plus the two handoff seeds.

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
| *(none)* | ingest + tag + build from your real OpenCode sessions, copy `snapshot.json`, write the orchestrator JSON |
| `--reset` | wipe the derived database first, then re-ingest everything |
| `--no-collect` | skip the OpenCode ingest; only refresh the orchestrator JSON from the seeds (instant) |

---

## What it shows

| Area | Chart | Source |
| --- | --- | --- |
| **Orchestrator** | dual-agent async pipeline + seed 00/01 status | `seeds/*.md` |
| KPIs | agent time, your time, prompts, tokens, cost, sessions | snapshot |
| **When** | theme × time heatmap (agent time vs your time) | snapshot |
| **Where the tokens went** | token **Sankey**: tokens → agent → theme → work kind | snapshot |
| **Themes over time** | theme **stream** | snapshot |
| **Topic map** | topic **circle-pack** (deeper fill = rising) | snapshot |
| Terms / Work mix / Agents at once / Tools | rising–fading terms, busy time by kind, concurrency, tool calls | snapshot |
| **Subagents** / **Subagent runs** | runs by type · outcome, and when × how long · by model | OpenCode `task` tool calls + child sessions |

The **Subagents** charts are where the dual-agent orchestration shows up in real data: OpenCode logs every `task` call (`agent-plan`, `agent-coding`, `orchestrator`) as a subagent run.

Hover any chart for details; the `24H / 7D / 1MO / 1Y` buttons re-render for that range.

---

## Files

```
visualization/
  kdwpc.html             KD-WPC dashboard (rebranded upstream dev/index.html + orchestrator panel)
  kdwpc_collect.py       wrapper: runs the collector, copies the snapshot, writes the orchestrator JSON
  run.cmd                Windows one-click: collect → serve → open browser
  LICENSE                upstream MIT license (Angus Forbes)
  vendor/
    odv.py               upstream collector (stdlib only), KD-WPC-patched — see below
    charts.js            upstream Canvas 2D chart engine (unchanged)
  data/                  generated — gitignored (snapshot.json, kdwpc_orchestrator.json)
```

---

## KD-WPC changes vs upstream

`vendor/odv.py` — all changes are Windows/data-format robustness, semantics unchanged:

1. **Windows privacy gate.** Upstream fails closed on Windows (`os.getuid()` / `chmod 0o700` are POSIX-only). Guarded behind `os.name == "nt"`.
2. **`%-m/%-d` strftime.** POSIX-only format specifier crashed `build` on Windows (`ValueError`). Replaced with a portable month/day string.
3. **Structured tool queries.** `call_of()` assumed `query` was a string; real OpenCode logs contain calls whose `query` is a **dict** (e.g. `cloudflare-observability_query_worker_observability`), which crashed ingest with `KeyError: slice(None, 160, None)`. Non-string queries are now safely serialised.
4. **New OpenCode schema (`session_v2` / `session_message`).** Newer OpenCode moved sessions out of `session`/`message`/`part` into `session_v2` + `session_message`. Upstream only reads the old tables, so on this machine it silently stopped at the schema upgrade and saw **nothing after Sep 26**. The collector now reads both schemas, maps the v2 message `content` parts and part-level `time` to the upstream shape, and uses the v2 `session.agent` field (`plan` / `build` / `orchestrator`) for subagent-type labels.
5. **`KDWPC_DATA` env override** for the derived data directory (defaults to `~/.local/share/kdwpc-agent-activity`).

`kdwpc.html` / `kdwpc_collect.py` — new: the orchestrator strip, the collector wrapper, and the browser layout. `charts.js` is untouched.

---

## Data & privacy

- **Real local data.** The collector reads your OpenCode store (`~/.local/share/opencode` — override with `OPENCODE_DATA_DIR`) **read-only**; it never modifies OpenCode's database.
- Derived data (a small SQLite DB + snapshot) lives in `~/.local/share/kdwpc-agent-activity/` and `visualization/data/`. The latter is **gitignored**, so nothing derived is committed.
- Tagging uses **rules only** (`jev: false`) — no AI calls. (Optional Jev integration from upstream isn't wired in here; the kit's JEV is env-only and stubbed until a Typesafe key is provided.)

---

## Attribution & license

Charts, collector, and the dashboard concept are by **Angus Forbes** — MIT, see [`LICENSE`](./LICENSE). The KD-WPC adaptation (orchestrator panel, collector wrapper, Windows/data fixes) is part of the `wpc2-dual-agent` kit.

Upstream project: <https://github.com/angusforbes/omarchy-agent-activity-visualization>
