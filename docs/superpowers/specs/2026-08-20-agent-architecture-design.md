# Vendor-neutral agent architecture: anatomy, agent card, and conversational variant

**Status:** approved in chat (mockups validated 2026-08-20)
**Date:** 2026-08-20
**Scope:** `skills/automation-design/references/automation-primitives.md` (new Agent anatomy section + vendor lexicon), `semantic-patterns.md` (one new pattern, one extended pattern, counter 18→19), `type-flowchart.md` (one detail-set rule addition), `SKILL.md` (routing row + description hooks, mirrored into the four plugin manifests), two new example assets + gallery tabs, ADR 0002 amendment, minor version bump. No new visual type, no new color role, no changes to `mxgraph_emit.py` / `drawio_extract.py` / import flows.

## 1. Context

The skill models agents (primitives: Agent, Tool, LLM, MEM, KB, Approval; patterns 13–17) but cannot yet express four things a client-facing agent architecture document needs, regardless of whether the agent is built in UiPath, Copilot Studio / Power Automate, LangChain/LangGraph, or plain code:

1. **Operating mode** — the ✦ AGENT badge says a node reasons; nothing says *how it is engaged* — triggered autonomously, conversing with a human, or invoked as a step. (The review that shaped this renamed the axis from "autonomy level": AUTO describes triggering, CONV interaction, STEP invocation — one chip per agent picks the dominant engagement, and the sublabel carries nuance.)
2. **The I/O contract** — what enters the agent and what it produces is nowhere structural.
3. **Context grounding** — KB exists as a store, but "grounding" as a mechanism (sources retrieved into the agent's context, visually distinct from tools the agent *acts* through) is unnamed.
4. **The conversational agent** — pattern 11 covers approval suspensions and pattern 3 covers conversation→artifact, but not "a user converses with an agent that grounds each answer and can hand the session to a human."

Design was iterated visually with the user (mockups v1–v4 in `experiments/agent-mockups/`, gitignored). Three decisions came out of that iteration and are binding:

- **The unified card layout.** One spatial grammar for every agent: a horizontal **I/O spine** (IN node → agent → OUT node, ink strokes — the page's dominant read), LLM above (PROMPT), a **CONTEXT GROUNDING container** below-left (reads, dashed RETRIEVE edges), the **TOOL PERMISSIONS boundary** below-right (acts, link-blue TOOL CALL edges), and the **escalation human** below-center (dashed accent ESCALATE). Reading: *horizontal = data flow; lower-left = knowledge; lower-right = action; top = reasoning; bottom = the human*.
- **The conversational agent is the same card**, not a different diagram: `CONV` chip, IN = user query (per turn), OUT = answer + source, escalation = a human takes over the session. Turn-by-turn dynamics, when timing matters, are drawn as a **Sequence directly** (pattern 11 only when the suspension/handoff is the story) — no second new pattern.
- **No containers for escalation or guardrails.** Containers mean *reach*; escalation targets are alternative exits (≤2 inline, each edge labeled with its condition; 3+ routes are an escalation *policy* → a dedicated decision **Flowchart**; pattern 15 applies only when the escalation belongs to a multi-agent topology) and guardrails are *controls on paths*, drawn as (a) a `GUARDRAILS · …` inventory line in the page-context panel and (b) an on-edge **guardrail gate** marker on the specific edge each control governs; full control inventories route to pattern 17. The tool-permission boundary is itself the permissions guardrail — a separate "guardrails" frame would duplicate it.

## 2. Decision

### 2.1 Agent anatomy (new section in `automation-primitives.md`)

**Operating modes** — a closed set of three, drawn as a second chip beside the agent's `✦ AGENT` tag (same chip geometry as the type tag; accent-tinted like the agent's other chips). The axes differ (AUTO = triggering, CONV = interaction, STEP = invocation); the chip names the *dominant engagement mode*, and edge cases (a conversational agent that is also invokable) keep one chip and note the rest in the sublabel:

| Chip | Mode | Meaning |
|---|---|---|
| `AUTO` | Autonomous | Triggered by schedule/event/queue; runs unattended; decides and acts within its guardrails |
| `CONV` | Conversational | A human is in the loop each session; the agent answers turn by turn |
| `STEP` | Invoked | Called as one step inside a workflow and returns a result |

Vendor-neutral by construction (UiPath agent activity, Copilot Studio topic, LangGraph graph invoked from code are all `STEP`; an autopilot inbox agent is `AUTO`; a chat copilot is `CONV`). Do not invent a fourth mode — pick the closest and let the sublabel carry nuance.

**I/O contract.** On an agent card, the contract is structural: an **IN node** (Input/User treatment, `IN` chip) and an **OUT node** (`OUT` chip, white/ink treatment) on the horizontal spine, connected to the agent with ink-stroke arrows labeled with the payload kind (`EVENT`, `QUERY` → `RESULT`, `ANSWER`). In topology diagrams (pattern 13), the contract compresses to one sublabel line: `in: email json → out: draft + log`.

**Grounding vs. tools.** Grounding is an **edge kind**, not a node kind: dashed muted edges labeled `RETRIEVE` from existing source primitives (KB, DOC, APP-read-only, MEM) *into* the agent. Tools stay link-blue `TOOL CALL` edges *out of* the agent. New container primitive: **grounding container** — `ink @ 0.03` fill, `ink @ 0.30` dashed `4,4` stroke, mono uppercase eyebrow `CONTEXT GROUNDING · N` — grouping the sources, mirror-symmetric to the tool-permission boundary (which keeps its accent Security/Boundary treatment and doubles as the permissions guardrail).

**Guardrail gate** — a small marker on the edge a control governs: `16×16 rx=3` chip, paper fill, `soft` stroke, with a mono label under it naming the control. The glyph inside names the **enforcing class**, consistent with the badge convention and with pattern 17's enforcement actors: `◉` for a human gate (`APPROVAL`, `CONSENT`), `⚙` for an automated one (`PII FILTER`, `RATE LIMIT`). Plus one `GUARDRAILS · …` line in the page-context panel as the inventory. Full inventories route to pattern 17 (Layer stack).

**Escalation rule.** ≤2 escalation edges per figure, each dashed-accent and labeled with its condition (`CONF < 70%`); the target is a named human role, never an anonymous inbox. Three or more escalation routes are an escalation policy: link a dedicated decision **Flowchart** (conditions → owners); use pattern 15 only when the escalation belongs to a multi-agent topology. Never an escalation container.

**Vendor lexicon** — a translation table so imports and generation map platform terms onto the neutral vocabulary (names go in sublabels, never in chips):

| Concept (neutral) | UiPath | Microsoft (Copilot Studio / Power Automate) | LangChain / LangGraph | Plain code |
|---|---|---|---|---|
| Agent | Agent / Autopilot | Copilot Studio agent | agent graph / `create_agent` | agent loop |
| Invoked unit (`STEP`) | agent activity in a workflow | topic / agent flow | node / subgraph | function call |
| Tool | tool (workflow, API, activity) | action / connector / flow | tool, @tool function | function |
| Context grounding | Context Grounding index | knowledge source | retriever / RAG chain | retrieval query |
| Memory | agent memory | conversation history | checkpointer / memory | state store |
| Trigger (AUTO) | Orchestrator trigger | Power Automate trigger | cron / event handler | scheduler |
| Session (CONV) | conversation | conversation session | thread | chat session |
| Guardrail | governance policy | content moderation / DLP | guardrail lib / validator | assertion / filter |
| Escalation | Action Center task | handoff to (human) agent | interrupt / human-in-loop node | ticket / notification |

### 2.2 New semantic pattern 19: **Agent card** → Architecture

**Selection triggers:** One agent must be documented as its architecture artifact — charter, operating mode, I/O contract, what it reads, what it may do, and where a human takes over. The client-facing "anexă de soluție" for an agent built on any platform.

**Required primitives:** Page-context panel (`AGENT CARD` eyebrow; `CHARTER`, `MODE`, `GUARDRAILS` lines); the I/O spine (IN node → agent with `✦ AGENT` + operating-mode chip → OUT node); LLM node with `PROMPT` edge; grounding container with ≥1 source and `RETRIEVE` edges; tool-permission boundary with ≥1 tool and `TOOL CALL` edges; ≤2 escalation edges to named human roles; on-edge guardrail gates where a control bites.

**Conversational variant:** `CONV` chip; IN = the user's query (per turn), OUT = the answer (+ source); escalation reads "human takes over the session"; the `MODE` panel line says turn-based. When turn timing or session dynamics are the story, draw that figure as a **Sequence directly** (patterns are optional; the type owns the layout) — reach for pattern 11 only when a suspension/handoff *is* the story. The card stays the static architecture view.

**Budget:** 1 agent, ≤4 grounding sources, ≤5 tools, ≤2 escalation targets, ≤2 guardrail gates, 2 containers, and **≤14 primary nodes total** (the spine's IN/OUT, the LLM, and each human count; containers and gates don't). The two containers are the card's sanctioned zoning above the 9-node target — the same mechanism as the blueprint's phase banding — and the ceiling is absolute: a busier agent splits its tool inventory into a linked pattern-13 or pattern-17 figure rather than growing the card. Category maxima are non-composable — the 14-node total always wins (e.g. 4 sources + 5 tools forces dropping the second human or gate-owner node).

**Anti-patterns:** an escalation or guardrails *container*; grounding invisible ("magic answers"); grounding sources styled as tools; vendor product names in chips; a second accent (the agent is the focal element; the escalation edge may share the accent as its continuation); operating-mode chip omitted so the reader can't tell a copilot from an autopilot; a `⚙`-class control drawn with the `◉` glyph (the gate glyph states the enforcing class, and `◉` means human).

**Static fallback:** everything above readable in one frame — the card is static by definition.

### 2.3 Pattern 13 (**Agent with tools**) extension

Required primitives gain: the operating-mode chip on the agent; `RETRIEVE` edges (dashed) visually distinct from `TOOL CALL` edges (link-blue); the one-line I/O sublabel. The grounding container becomes the sanctioned grouping when the agent has ≥2 sources. Budgets unchanged.

### 2.4 Agent card as a detail-set annex page (`type-flowchart.md`)

One rule added to § Detail set: a set may include **non-flowchart annex pages** — the agent card (Architecture layout) is the first — carrying the same canonical numbering, footer colophon, `↑ parent` / `CALLED FROM` links, and `self_check.py --set` verification as every other page — noting the verifier's scope: it checks link-target existence, fragment resolution, and filename-number uniqueness only; concordance of the in-page title, number, colophon, and `CALLED FROM` list stays in the taste gate / detail-set consistency rule. The invoking activity box on a process page (an `AGENT`-tagged step) is the forward SVG link to the card, exactly like a sub-process link. The page-context panel primitive defined there is explicitly reusable by annex pages.

## 3. Non-goals

- **No new visual type** (ADR 0002/0007 — the card routes to Architecture; the count stays 11).
- **No second new pattern for conversational sequence dynamics** — pattern 11 already owns suspension/handoff on Sequence; the card's variant note routes to it.
- **No changes to `mxgraph_emit.py`, `drawio_extract.py`, or the import flow.**
- **No new style-guide color role** — the spine uses `ink`, grounding uses existing ink-opacity treatments, gates use `soft`.

## 4. Files touched

- `skills/automation-design/references/automation-primitives.md` — new **Agent anatomy** section (operating-mode chips, I/O contract, grounding edge kind + container, guardrail gate, escalation rule) + **vendor lexicon** table.
- `skills/automation-design/references/semantic-patterns.md` — pattern 19 section + routing-table row (`One agent's charter, operating mode, I/O, grounding, tools, and escalation` → **Agent card** → Architecture); pattern 13 required-primitives extension; intro sentence "Patterns 8–18" → "8–19".
- `skills/automation-design/references/type-flowchart.md` — the annex-page rule in § Detail set.
- `skills/automation-design/SKILL.md` — routing-table row in §3; frontmatter description gains lexical hooks (`conversational agents`, `context grounding`, `operating modes and autonomy`); the same description string updated verbatim in `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, and both marketplace manifests (docs-sync enforces parity).
- `scripts/verify-semantic-motion.py` — pattern counter 18 → 19, amended in the same commit as:
- `docs/adr/0002-semantic-patterns-do-not-expand-the-taxonomy.md` — amendment recording pattern 19 (routes to Architecture; type count unchanged).
- New assets: `skills/automation-design/assets/example-agent-card.html` (AUTO — the invoice answer agent from the validated v4 mockup) and `skills/automation-design/assets/example-agent-card-conversational.html` (CONV — the support chat agent), both passing the full gate suite; two gallery tabs in `assets/index.html`. Colophons in these standalone examples carry plain text (no `href="#"` placeholders).
- Version bump minor (0.2.0 → 0.3.0) via `scripts/bump-plugin-version.py --minor`.

## 5. Verification impact

- `verify-semantic-motion.py --markdown-only` moves to 19 patterns / 11 types; `verify-docs-sync.py` checks the new description hooks and gallery reachability; both must pass with the ADR amendment in the same change.
- New assets pass `self_check.py`, `verify-geometry.py --all`, `lint-skin.py --all --baseline`, and the SKILL.md §9 taste gate.
- `verify-plugin-package.py` satisfied by the minor bump.

## 6. Open questions / future work

- Whether multi-agent solutions want a "team card" (supervisor + worker cards linked in one set) — pattern 15 + detail-set numbering already compose for this; revisit if a real document needs more.
- Whether the vendor lexicon should grow per-platform packs (icons, naming presets) — out of scope; the table is guidance, not configuration.
