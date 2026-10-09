# MEMORY_SCOPE.md
> `.AGENTS/_DUAL-AGENTS/MEMORY_SCOPE.md`

How the Dual-Agent kit persists long-term memory in the **DGUI-HyperMem** MCP.

---

## Scope (per-project)

- Scope name: **`wpc2-dual-agent`**
- All WPC2 memory writes go to this scope — **not** the shared `default` scope.
- Scope is set per call: `search({ scope: "wpc2-dual-agent", ... })`.

---

## The one rule that matters: the salience gate

DGUI-HyperMem only *surfaces* memories whose JEV `salience` is **≥ ~3.0**.
Lower-salience writes are stored but come back `active: false` and are **never**
returned by `search` or `list` (they are effectively invisible).

Consequences:

1. Write **one rich, high-signal `project` memory** — not many small ones.
   A solution/lesson note at `salience 2.4–2.9` will be stored and lost.
2. High-signal content = concrete structure, facts, defaults, decisions, verified
   procedures. Short or conversational notes score low.
3. **Verify after writing** (see below). If it does not surface, enrich and re-add.

---

## Current memory

| field | value |
| --- | --- |
| scope | `wpc2-dual-agent` |
| id | `c0294583-ff5b-43ae-8283-699b2ea4c0b8` |
| type | `project` |
| salience | 3.72 |
| durable | 0.94 |

It holds: the scaffold tree, stack/viewport defaults, the three ruleset additions
(Excalidraw parser step, Imports/Tools note, Browser Capture Flow), the parsed
`kd_wpc_2-1.excalidraw` wireframe, and the two verified session facts
(BrowserOS neo → GitHub REST + git fallback; `.gitignore *.png` publishing hygiene).

---

## Write / verify

```js
// write one comprehensive memory
await tools["dgui-hypermem"].add({
  scope: "wpc2-dual-agent",
  content,                    // dense, factual, structured
  tags: ["wpc2", "dual-agent", "project", ...],
  corpus_type: "universal",
});

// verify it ACTIVATED and is retrievable
const p = await tools["dgui-hypermem"].profile({ scope: "wpc2-dual-agent" }); // expect active >= 1
const r = await tools["dgui-hypermem"].search({ scope: "wpc2-dual-agent", query }); // expect a hit
```

If `active` does not increase, the memory scored below the gate — fold its facts
into the existing comprehensive memory (or re-add a richer one) instead of leaving
an invisible row.

---

## Rules

- **No secrets** — no keys, tokens, or credentials in memory content.
- **No fabricated JEV** — if `JEV_API_KEY` is unset, JEV items are
  `PENDING_TYPESAFE_API_KEY`; do not invent results.
- Keep it factual: repo, structure, defaults, decisions, verified procedures.
