# Agent Architecture (Agent Card, Autonomy, Grounding) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add vendor-neutral agent-architecture support: agent anatomy primitives (operating-mode chips, I/O contract, grounding, guardrail gates, escalation rule, vendor lexicon), a new **Agent card** semantic pattern (18→19) with a conversational variant, detail-set annex pages, and two example assets built from the user-validated v4 mockups.

**Architecture:** Documentation-first: one new section + table in `automation-primitives.md`, one new pattern section + one extension in `semantic-patterns.md` (counter and ADR amendment move together), one rule in `type-flowchart.md`, routing/description hooks in `SKILL.md` mirrored into three manifest slots, then the two assets hardened from `experiments/agent-mockups/` to pass every gate.

**Tech Stack:** Markdown references, hand-authored SVG-in-HTML assets, existing Python verifier suite.

**Spec:** `docs/superpowers/specs/2026-08-20-agent-architecture-design.md`

## Global Constraints

- Branch: all commits on `feature/agent-architecture`; main receives one final squash-merge (repo convention).
- No new visual type, no new color role, no changes to `mxgraph_emit.py` / `drawio_extract.py` / import flows (spec §3).
- Pattern counter moves 18→19 **in the same commit** as the ADR 0002 amendment (ADR-mandated procedure).
- Operating-mode chips are the closed set `AUTO` / `CONV` / `STEP` (the category is *operating mode*, never "autonomy level" — the axes differ); grounding container = `ink @ 0.03` fill, `ink @ 0.30` dashed `4,4` stroke; guardrail gate = `16×16 rx=3`, paper fill, `soft` stroke, glyph = enforcing class (`◉` human / `⚙` automated); escalation ≤2 labeled edges, never a container (3+ routes → a dedicated decision Flowchart).
- Agent-card budget: ≤14 primary nodes total; 1 agent, ≤4 sources, ≤5 tools, ≤2 escalations, ≤2 gates, 2 containers (spec §2.2).
- Asset rules: all coords divisible by 4; SKILL.md §6 connector rules; title/desc IDs must equal `<file-stem-minus-example->-title/-desc` (lint-skin); no `href="#"` anywhere; standalone colophons are plain text.
- Known trap: `build-icons.py` regenerates two files with EOL-whitespace-only diffs — `git checkout --` them, never commit.
- Repo root: `/mnt/d/projects/automation-design`.

---

### Task 1: Agent anatomy + vendor lexicon in `automation-primitives.md`

**Files:**
- Modify: `skills/automation-design/references/automation-primitives.md` (insert after the `## Badge convention…` section, before `## Edge kinds`)

**Interfaces:**
- Produces: the section heading `## Agent anatomy` and the chip names `AUTO`/`CONV`/`STEP`, the edge label `RETRIEVE`, the container eyebrow `CONTEXT GROUNDING · N`, and the guardrail-gate geometry — cited verbatim by Tasks 2 and 4.

- [ ] **Step 1: Insert the Agent anatomy section**

Insert this block between the badge-convention section and `## Edge kinds`:

````markdown
## Agent anatomy — operating mode, I/O, grounding, guardrails

Four conventions that make one agent legible on any platform. The **agent card** pattern ([semantic-patterns.md §19](semantic-patterns.md)) requires all of them; topology diagrams (pattern 13) use the compressed forms noted below.

**Operating modes.** A closed set of three, drawn as a second chip beside the agent's `✦ AGENT` tag (same chip geometry; accent-tinted like the agent's other chips). The axes differ — `AUTO` describes triggering, `CONV` interaction, `STEP` invocation — so the chip names the *dominant engagement mode*; edge cases (a conversational agent that is also invokable) keep one chip and note the rest in the sublabel. Do not invent a fourth mode.

| Chip | Mode | The reader may assume |
|---|---|---|
| `AUTO` | Autonomous | Triggered by schedule/event/queue; runs unattended; decides and acts within its guardrails |
| `CONV` | Conversational | A human is in the loop each session; the agent answers turn by turn |
| `STEP` | Invoked | Called as one step inside a workflow; returns a result and stops |

**I/O contract.** On an agent card the contract is structural: an **IN node** (Input/User treatment, `IN` chip) and an **OUT node** (`OUT` chip, white fill, `ink` stroke) on a horizontal spine through the agent, ink-stroke arrows labeled with the payload kind (`EVENT`, `QUERY` → `RESULT`, `ANSWER`). In topology diagrams it compresses to one sublabel line: `in: email json → out: draft + log`.

**Grounding is an edge kind, not a node kind.** Sources stay the existing primitives (KB, DOC, MEM, a read-only APP); what makes them *grounding* is the dashed muted edge labeled `RETRIEVE` running **into** the agent — visually distinct from the link-blue `TOOL CALL` edges running **out of** it. When an agent has ≥2 sources, group them in a **grounding container**: `ink @ 0.03` fill, `ink @ 0.30` dashed `4,4` stroke, `rx=8`, mono uppercase eyebrow `CONTEXT GROUNDING · N` — mirror-symmetric to the tool-permission boundary, which keeps its Security/Boundary treatment and *is* the permissions guardrail.

**Guardrail gates.** A guardrail is a control on a path, never a region. Draw it where it bites: a `16×16 rx=3` chip (paper fill, `soft` stroke) sitting on the governed edge, with a mono label naming the control. The glyph inside names the **enforcing class**, consistent with the badge convention and pattern 17's enforcement actors: `◉` for a human gate (`APPROVAL`, `CONSENT`), `⚙` for an automated one (`PII FILTER`, `RATE LIMIT`). Plus one `GUARDRAILS · …` inventory line in the page-context panel. A full control inventory routes to the **Automation guardrails and boundaries** pattern — never a "guardrails" container.

**Escalation.** ≤2 escalation edges per figure, each dashed-accent, labeled with its condition (`CONF < 70%`), targeting a *named human role*. Three or more routes are an escalation policy: link a dedicated decision **Flowchart** (conditions → owners); use Supervisor-and-workers only when the escalation belongs to a multi-agent topology. Never an escalation container — targets are alternative exits, not a shared boundary.

### Vendor lexicon

Translation guidance between the neutral vocabulary and common platforms. Platform names go in sublabels, never in chips or node names.

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
````

- [ ] **Step 2: Verify links and sync**

Run: `python3 scripts/verify-docs-sync.py`
Expected: PASS (the new `semantic-patterns.md` relative link resolves; §19 doesn't exist yet but the link check is file-level, not anchor-level).

- [ ] **Step 3: Commit**

```bash
git add skills/automation-design/references/automation-primitives.md
git commit -m "docs: add agent anatomy (operating modes, I/O, grounding, guardrail gates) and vendor lexicon"
```

---

### Task 2: Pattern 19 + pattern 13 extension + counter + ADR amendment

**Files:**
- Modify: `skills/automation-design/references/semantic-patterns.md`
- Modify: `scripts/verify-semantic-motion.py` (PATTERN_NAMES tuple + the "18 semantic patterns" OK string)
- Modify: `docs/adr/0002-semantic-patterns-do-not-expand-the-taxonomy.md` (amendment)

**Interfaces:**
- Consumes: Task 1's section heading and chip/edge names, cited verbatim.
- Produces: the pattern name **`Agent card`** exactly as written in PATTERN_NAMES (Task 4's assets illustrate it; SKILL.md's routing row in Task 3 names it).

- [ ] **Step 1: Update the intro and routing table**

In `semantic-patterns.md`: change `Patterns 8–18 model automation behavior` to `Patterns 8–19 model automation behavior`, and append this routing-table row after the RPA solution blueprint row:

```markdown
| One agent's charter, operating mode, I/O contract, grounding, tools, and escalation | **Agent card** | Architecture |
```

- [ ] **Step 2: Append the §19 section**

Insert before `## Composition rules`:

````markdown
## 19. Agent card

**Selection triggers:** One agent must be documented as its architecture artifact — charter, operating mode, I/O contract, what it reads, what it may do, and where a human takes over. The client-facing solution annex for an agent built on any platform (UiPath, Copilot Studio, LangGraph, plain code — the vendor lexicon in [automation-primitives.md](automation-primitives.md) maps the terms).

**Required primitives:** Page-context panel (`AGENT CARD` eyebrow; `CHARTER`, `MODE`, `GUARDRAILS` lines); the **I/O spine** — IN node → agent (✦ AGENT + operating-mode chip) → OUT node, ink strokes, payload labels (`EVENT`/`QUERY` → `RESULT`/`ANSWER`); LLM node with a `PROMPT` edge; **grounding container** with ≥1 source and dashed `RETRIEVE` edges in; **tool-permission boundary** with ≥1 tool and link-blue `TOOL CALL` edges out; ≤2 dashed-accent escalation edges to named human roles, each labeled with its condition; on-edge guardrail gates where a control bites. The fixed spatial grammar carries the meaning: *horizontal = data flow; lower-left = knowledge; lower-right = action; top = reasoning; bottom = the human.*

**Conversational variant:** `CONV` chip; IN is the user's query (per turn), OUT the answer (+ source); escalation reads "human takes over the session"; the `MODE` panel line says turn-based. When turn timing or session dynamics are the story, draw that figure as a **Sequence directly** — reach for **Human-in-the-loop approval** only when a suspension or handoff is the story. The card stays the static architecture view.

**Complexity budget:** 1 agent, ≤4 grounding sources, ≤5 tools, ≤2 escalation targets, ≤2 guardrail gates, 2 containers, **≤14 primary nodes total** (IN, OUT, LLM, and each human count; containers and gates don't). The two containers are the card's sanctioned zoning above the nine-node target — the same mechanism as the blueprint's phase banding — and the ceiling is absolute: category maxima are non-composable — the 14-node total always wins (4 sources + 5 tools forces dropping a human or gate-owner node). A busier agent splits its inventory into a linked Agent-with-tools or guardrails figure rather than growing the card.

**Anti-patterns:** An escalation or guardrails *container*; grounding invisible so answers look like magic; grounding sources styled as tools; vendor product names in chips; a second accent (the agent is focal; the escalation edge may share the accent as its continuation); the operating-mode chip omitted so a copilot is indistinguishable from an autopilot; a `⚙`-class control drawn with the `◉` glyph (the gate glyph states the enforcing class, and ◉ means human).

**Static fallback:** The card is static by definition — panel, spine, both containers, and every edge label readable in one frame.

**Nearest visual type:** **Architecture**. As a page inside a detail set, the card is a non-flowchart annex page carrying the set's numbering and navigation ([type-flowchart.md § Detail set](type-flowchart.md)).
````

- [ ] **Step 3: Extend pattern 13's required primitives**

In §13 (Agent with tools), replace the Required-primitives sentence with:

```markdown
**Required primitives:** Agent (✦ AGENT) with its **operating-mode chip** (`AUTO`/`CONV`/`STEP`) and charter in the sublabel, plus a one-line I/O contract (`in: … → out: …`); LLM; named tools with type tags; the permission boundary around the permitted toolset; data stores the agent reads — drawn as dashed `RETRIEVE` grounding edges, visually distinct from link-blue tool calls, grouped in a grounding container when there are ≥2 sources ([automation-primitives.md § Agent anatomy](automation-primitives.md)); the human or system that receives the result.
```

- [ ] **Step 4: Move the counter with the ADR amendment**

In `scripts/verify-semantic-motion.py`: append `"Agent card",` to `PATTERN_NAMES` (after `"RPA solution blueprint",`) and change the OK string `"OK: 18 semantic patterns route independently to the preserved 11 visual types"` to say `19`. In ADR 0002, append an amendment:

```markdown
**2026-08-20 — the pattern count is 19; the type count is still 11.** **Agent card** was added, routing to the existing **Architecture** type: one agent documented as its architecture artifact (operating-mode chip, I/O spine, grounding container, tool boundary, guardrail gates, escalation). No new layout grammar — the counter in `verify-semantic-motion.py` moved 18 → 19 in the same commit as this amendment, per the procedure above.
```

- [ ] **Step 5: Verify**

Run: `python3 scripts/verify-semantic-motion.py --markdown-only && python3 scripts/verify-docs-sync.py`
Expected: `OK: 19 semantic patterns route independently to the preserved 11 visual types` and docs-sync PASS. If the verifier flags a missing field in §19, it names which of the six required field labels is absent — fix the section, not the verifier.

- [ ] **Step 6: Commit (counter + ADR together)**

```bash
git add skills/automation-design/references/semantic-patterns.md scripts/verify-semantic-motion.py docs/adr/0002-semantic-patterns-do-not-expand-the-taxonomy.md
git commit -m "feat: add Agent card semantic pattern (18->19) with conversational variant; extend pattern 13"
```

---

### Task 3: Detail-set annex rule + SKILL.md routing/description + manifests

**Files:**
- Modify: `skills/automation-design/references/type-flowchart.md` (§ Detail set rules list)
- Modify: `skills/automation-design/SKILL.md` (§3 routing table + frontmatter description)
- Modify: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.codex-plugin/plugin.json` (`description` — and `longDescription` in the codex file — must repeat the SKILL.md description verbatim; docs-sync enforces it)

**Interfaces:**
- Consumes: the pattern name `Agent card` (Task 2).

- [ ] **Step 1: Add the annex-page rule**

In `type-flowchart.md` § Detail set, append to the "Rules that make it one deliverable" bullet list:

```markdown
- **Annex pages may use another visual type.** A set may include non-flowchart annex pages — the first is the **agent card** ([semantic-patterns.md §19](semantic-patterns.md), Architecture layout) — carrying the same canonical numbering, colophon, `↑ parent` / `CALLED FROM` links, and `self_check.py --set` verification as every other page — the verifier checks link existence, fragments, and filename-number uniqueness only; concordance of in-page title, number, colophon, and `CALLED FROM` stays in the taste gate and the set-consistency rule. The invoking `AGENT`-tagged activity box is the forward SVG link to the card, exactly like a sub-process link, and the page-context panel defined here is reusable on annex pages.
```

- [ ] **Step 2: Add the SKILL.md routing row**

In SKILL.md §3's behavioral-trigger table, append after the RPA solution blueprint row:

```markdown
| One agent's charter, operating mode (autonomous / conversational / invoked), I/O, context grounding, tools, escalation | **Agent card** → Architecture |
```

- [ ] **Step 3: Extend the frontmatter description with the lexical hooks**

In the SKILL.md frontmatter description, change the fragment `agent tools, multi-agent supervision, guardrails and automation boundaries` to `agent tools, conversational agents, agent operating modes and autonomy, context grounding, multi-agent supervision, guardrails and automation boundaries`, then paste the resulting full description string **verbatim** into: `.claude-plugin/plugin.json` (`description`), `.claude-plugin/marketplace.json` (`description`), `.codex-plugin/plugin.json` (`description` and `longDescription`).

- [ ] **Step 4: Verify parity**

Run: `python3 scripts/verify-docs-sync.py`
Expected: PASS (description hooks + manifest parity + all links).

- [ ] **Step 5: Commit**

```bash
git add skills/automation-design/references/type-flowchart.md skills/automation-design/SKILL.md .claude-plugin/plugin.json .claude-plugin/marketplace.json .codex-plugin/plugin.json
git commit -m "docs: agent-card routing row, description hooks, detail-set annex-page rule"
```

---

### Task 4: Example assets from the validated mockups + gallery tabs

**Files:**
- Create: `skills/automation-design/assets/example-agent-card.html` (from `experiments/agent-mockups/mock-agent-card.html`, the AUTO invoice agent)
- Create: `skills/automation-design/assets/example-agent-card-conversational.html` (from `experiments/agent-mockups/mock-conversational-agent.html`, the CONV support chat agent)
- Modify: `skills/automation-design/assets/index.html` (two tabs)
- Modify: `skills/automation-design/references/semantic-patterns.md` — no change needed (patterns don't list examples); instead add both files to `type-architecture.md`'s Examples list? **No** — examples lists live in type references only when shipped for that type; check `type-architecture.md`'s Examples section and append the two entries there:

```markdown
- `assets/example-agent-card.html` — agent card (pattern 19: I/O spine, grounding container, tool boundary, guardrail gate, escalation)
- `assets/example-agent-card-conversational.html` — conversational agent card (CONV chip, user query → answer, human takes over session)
```

**Interfaces:**
- Consumes: the validated v4 mockup geometry, Task 1's primitive specs.
- Produces: gallery tab types `agent-card` and `agent-card-conversational` (filenames `example-<type>.html` — the gallery reachability check requires this exact correspondence).

- [ ] **Step 1: Harden the AUTO card**

Copy the mockup to `example-agent-card.html` and fix: `<title>` to `Agent card · Architecture`; eyebrow drops `MOCKUP` (`Architecture · agent card · Automation Design`); SVG ids to `agent-card-title` / `agent-card-desc` (lint-skin slug rule) and `aria-labelledby` to match; colophon becomes plain text `agent card · standalone example — in a detail set this page carries numbering and parent links` (remove the two `href="#"` anchors); verify every coordinate is divisible by 4 and every label mask keeps the 6–10px gap; rename the panel line `AUTONOMY ·` to `MODE ·`; keep the guardrail gate (◉ is correct — APPROVAL is a human gate), escalation, and both containers exactly as validated.

- [ ] **Step 2: Harden the CONV card**

Same procedure on `example-agent-card-conversational.html`: ids `agent-card-conversational-title`/`-desc`; eyebrow `Architecture · agent card · conversational · Automation Design`; plain-text colophon; everything else as validated (CONV chip, QUERY/ANSWER spine labels, CONSENT gate — ◉, human — and "takes over the session"); rename the panel line `AUTONOMY ·` to `MODE ·`.

- [ ] **Step 3: Gallery tabs**

After the detail-set tabs in `assets/index.html`:

```html
        <button class="tab" data-type="agent-card" data-single>
          <span class="eyebrow">13g</span>Agent card · autonomous
        </button>
        <button class="tab" data-type="agent-card-conversational" data-single>
          <span class="eyebrow">13h</span>Agent card · conversational
        </button>
```

- [ ] **Step 4: Run every gate**

```bash
python3 skills/automation-design/scripts/self_check.py skills/automation-design/assets/example-agent-card.html skills/automation-design/assets/example-agent-card-conversational.html
python3 scripts/verify-geometry.py --all
python3 scripts/lint-skin.py --all --baseline
python3 scripts/test-lint-a11y.py
python3 scripts/verify-docs-sync.py
```

Expected: all PASS. Fix the asset, never the baseline.

- [ ] **Step 5: Visual check**

Serve `assets/` with `python3 -m http.server` and screenshot both files via Playwright; confirm the spine reads left→right, no connector grazes a box, gates sit on their edges, legends clear the diagram.

- [ ] **Step 6: Commit**

```bash
git add skills/automation-design/assets/example-agent-card.html skills/automation-design/assets/example-agent-card-conversational.html skills/automation-design/assets/index.html skills/automation-design/references/type-architecture.md
git commit -m "feat: add agent-card example assets (autonomous + conversational) and gallery tabs"
```

---

### Task 5: Version bump + full sweep + squash-merge

**Files:**
- Modify: `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json` (via `scripts/bump-plugin-version.py --minor`, never by hand)

- [ ] **Step 1: Bump and verify the package gates**

```bash
python3 scripts/bump-plugin-version.py --minor   # 0.2.0 -> 0.3.0
python3 scripts/test-plugin-package.py
python3 scripts/verify-plugin-package.py origin/main
```

Expected: all PASS.

- [ ] **Step 2: Full CI-equivalent sweep**

```bash
python3 scripts/test-lint-a11y.py && \
python3 scripts/verify-semantic-motion.py --markdown-only && \
python3 scripts/verify-semantic-motion.py --example-only && \
python3 scripts/verify-motion.py --shipped && \
python3 scripts/lint-skin.py --all --baseline && \
python3 scripts/verify-sequence-oauth.py && \
python3 scripts/verify-drawio-import.py && \
python3 scripts/verify-mermaid-import.py && \
python3 scripts/test-verify-motion.py && \
python3 scripts/verify-docs-sync.py && \
python3 scripts/test-verify-docs-sync.py && \
python3 scripts/test-self-check.py && \
python3 scripts/verify-geometry.py --all && \
python3 scripts/test-verify-geometry.py && \
python3 scripts/test-mxgraph-emit.py && \
echo ALL GREEN
```

Expected: `ALL GREEN`. If `build-icons.py` was run anywhere, `git checkout -- skills/automation-design/assets/icons.html skills/automation-design/references/primitive-icons.md` before committing.

- [ ] **Step 3: Commit the bump**

```bash
git add .claude-plugin/plugin.json .codex-plugin/plugin.json
git commit -m "chore: bump plugin version to 0.3.0 for agent architecture release"
```

- [ ] **Step 4: Squash-merge to main and push**

```bash
git checkout main
git merge --squash feature/agent-architecture
git commit   # single release message summarizing: agent anatomy, vendor lexicon, pattern 19 + conversational variant, pattern 13 extension, annex pages, 2 assets, 0.3.0
git push origin main
git branch -D feature/agent-architecture
```

---

## Self-review notes

- Spec coverage: §2.1 → Task 1; §2.2 + §2.3 + counter/ADR → Task 2; §2.4 + SKILL/manifests → Task 3; assets → Task 4; §5 verification + bump → Task 5. No unowned requirement.
- Name consistency: pattern name `Agent card` identical across PATTERN_NAMES, §19 heading, both routing rows; asset slugs `agent-card` / `agent-card-conversational` match file names and gallery `data-type` values; chip names `AUTO`/`CONV`/`STEP` and edge labels `RETRIEVE`/`TOOL CALL`/`PROMPT`/`ESCALATE` identical across Tasks 1, 2, 4.
- Non-goals respected: no task touches emitters, import flows, style-guide roles, or the type count.
