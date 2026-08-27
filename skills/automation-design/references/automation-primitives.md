# Automation primitives

The shared vocabulary for every automation diagram. Semantic patterns (rows 8–20 of the routing table) cite these primitives by name; this file defines what each one means, how it is drawn, and how edges between them are styled. Load it whenever an automation pattern routes.

[`../taxonomy.json`](../taxonomy.json) is the machine-readable source of truth for stable IDs, activity tags, and their mappings. This reference is the human-readable drawing contract; CI requires both projections to agree.

**Vendor-neutral by design.** The internal concept is `Queue`, never `UiPath Orchestrator Queue`. Platform names (UiPath, Power Automate, Automation Anywhere, LangGraph, …) belong in the technical **sublabel** (Geist Mono), never in the node name or the type tag. This keeps one diagram language across every client stack.

## Semantic axes — what it is vs. how it behaves

Classify every automation component on two independent axes. **Kind** answers what the component is; **behavior** answers how it acts. Display tags remain compact visual labels, not the ontology itself.

| Stable kind ID | Meaning |
|---|---|
| `kind.human` | A person applying judgment or performing manual work |
| `kind.robot` | An attended or unattended UI automation executor |
| `kind.workflow` | A deterministic orchestration or cloud-flow executor |
| `kind.agent` | A goal-directed component that selects actions through reasoning |
| `kind.model` | A probabilistic inference component without independent tool selection |
| `kind.service` | A programmatic capability or API endpoint |
| `kind.application` | A business or user-facing software system |
| `kind.orchestrator` | A control plane that schedules and assigns execution |
| `kind.queue` | A durable ordered collection of work items |
| `kind.trigger` | An event, schedule, or request that starts execution |
| `kind.tool` | A bounded capability exposed to an agent or workflow |
| `kind.datastore` | A passive store for state, memory, knowledge, or records |
| `kind.document` | A payload artifact such as a PDF, email, spreadsheet, or image |
| `kind.vault` | A protected store for secrets or credentials |
| `kind.observability` | A destination for audit, logs, traces, metrics, or run history |
| `kind.exception` | A failure outcome or recovery mechanism |

| Stable behavior ID | Meaning |
|---|---|
| `behavior.human` | Judgment or manual action performed by a person |
| `behavior.deterministic` | Rules and inputs select prescribed, repeatable steps |
| `behavior.probabilistic` | Statistical inference produces an output that may need a quality gate |
| `behavior.agentic` | The component reasons over a goal and chooses among permitted actions |
| `behavior.passive` | The component stores, exposes, or transports information without choosing work |

Do not infer kind from the presence of an LLM. A document classifier is `kind.model` + `behavior.probabilistic`; an agent that selects tools is `kind.agent` + `behavior.agentic`. Likewise, a cloud flow is `kind.workflow` + `behavior.deterministic`, while a desktop UI automation is `kind.robot` + `behavior.deterministic`.

## Node primitives

Each primitive maps to a node treatment from the design system (SKILL.md §5) plus a type tag. The tag is the rectangular chip in the node's top-left corner (Geist Mono, 7px, uppercase).

| Primitive | Type tag | Meaning | Node treatment |
|---|---|---|---|
| **Human** | `HUMAN` | Operator, approver, or business user performing manual steps | Input / User |
| **RPA Robot** | `RPA` | Deterministic execution — scripted UI or API steps, attended or unattended | Backend / API / Step |
| **Workflow** | `FLOW` | Deterministic orchestration without desktop UI automation | Backend / API / Step |
| **Agent** | `AGENT` | LLM-driven component that reasons and decides | Backend / API / Step (focal when the decision is the story) |
| **Model** | `MODEL` | Probabilistic inference that returns a result but does not select tools independently | External / Cloud |
| **Orchestrator** | `ORCH` | Scheduler / control plane that assigns work to robots or agents | Backend / API / Step |
| **Queue** | `QUEUE` | Ordered work items / transactions awaiting a consumer | Store / State |
| **Trigger** | `TRIG` | What starts the automation — schedule, event, email, webhook, API | Input / User |
| **Business App** | `APP` | Target system — ERP, CRM, browser app, legacy desktop | External / Cloud |
| **API** | `API` | Programmatic integration point | Backend / API / Step |
| **Tool** | `TOOL` | Capability exposed to an agent — function, MCP server, RPA workflow | Backend / API / Step |
| **Memory** | `MEM` | Agent short/long-term memory | Store / State |
| **Knowledge Base** | `KB` | RAG / document store the agent retrieves from | Store / State |
| **Human Approval** | `APPROVAL` | Suspension point where a person validates, approves, or rejects | Input / User (focal when the gate is the story) |
| **Credential Vault** | `VAULT` | Secrets store — never drawn as a plain data store | Security / Boundary |
| **Document** | `DOC` | Payload artifact — PDF, email, spreadsheet, image | Store / State |
| **Audit / Logs** | `AUDIT` | Telemetry, run history, evidence trail | Store / State |
| **Exception** | `EXC` | Business or system exception outcome | Optional / Async (dashed) |
| **Retry / DLQ** | `RETRY` | Recovery mechanism — retry policy, dead-letter queue | Optional / Async (dashed) |

Naming: the node name states the business role (`Invoice Performer`, `Exception Analyst`, `Finance Approver`); the sublabel states the technical detail (`unattended`, `gpt · tool-enabled`, `SAP FI`).

**`MODEL` is the only model-class tag.** Use it for an LLM, classifier, embedding model, or other probabilistic inference component; put the concrete model family or product (`GPT-5`, `Claude`, `invoice classifier`) in the node name or technical sublabel. `LLM` is a model subtype, not a second primitive or tag.

> **`EXC` vs. BE/SE codes.** `EXC` types an exception as an actor/outcome in topology diagrams (and `SYS EXC` / `ESCALATE` as edge labels). A PDD-style coded branch terminus inside a numbered flowchart page (`BE001`, `SE003`) is a different primitive — the **exception terminal** in [`type-flowchart.md`](type-flowchart.md) — and its codes never appear in an activity-tag chip.

## Activity tags — which system class owns this step

The table above types **actors and stores** in a topology diagram, where a node *is* a robot, queue, agent, or other component. A workflow diagram (flowchart, process, swimlane) is different: every box is a *step*, and its compact tag names the system class that executes, hosts, or receives that step. Because tags intentionally compress executors and resources into one visual slot, they never replace the underlying `kind` and `behavior` axes.

| Activity tag | Step meaning | Default kind · behavior of tagged system |
|---|---|---|
| `MAIL` | Read, send, or save attachments through mail | `kind.application` · `behavior.passive` |
| `DOC AI` | Digitize, classify, or extract a document | `kind.model` · `behavior.probabilistic` |
| `MODEL` | Infer, score, classify, or generate | `kind.model` · `behavior.probabilistic` |
| `AGENT` | Reason over a goal and select a permitted action | `kind.agent` · `behavior.agentic` |
| `HUMAN` | Validate, approve, correct, or handle an exception | `kind.human` · `behavior.human` |
| `RPA` | Execute scripted UI or API steps | `kind.robot` · `behavior.deterministic` |
| `FLOW` | Execute a workflow, cloud flow, or orchestration step | `kind.workflow` · `behavior.deterministic` |
| `API` | Call a programmatic endpoint | `kind.service` · `behavior.passive` |
| `APP` | Read from or write to a business application | `kind.application` · `behavior.passive` |
| `QUEUE` | Produce to or consume from a queue | `kind.queue` · `behavior.passive` |

Same vendor-neutral rule: `DOC AI`, never `Document Understanding`; `FLOW`, never `Power Automate`; `HUMAN`, never `Action Center`. The product name goes in the sublabel or the annotation. Do not invent a tag outside this set — pick the closest one and let the sublabel carry the specificity.

The mapping describes the **tagged system**, not the edge that invokes it. An API endpoint is therefore `kind.service` + `behavior.passive`; the caller carries the active behavior (`⚙ RPA`, `◆ FLOW`, or `✦ AGENT`), and the `API CALL` / `TOOL CALL` edge shows the invocation. This keeps the same API node passive in both workflow and topology views.

## Badge convention — kind and behavior at a glance

The reader must tell at a glance whether a box is a scripted robot, deterministic workflow, probabilistic model, agentic actor, human, or passive system. **In topology diagrams** (architecture, data flow, org chart — where the node is the actor) the tag carries a glyph prefix:

| Glyph + tag | Class | Behavior the reader may assume |
|---|---|---|
| `⚙ RPA` | Robot | Deterministic scripted UI or API execution |
| `◆ FLOW` | Workflow | Deterministic orchestration or cloud-flow execution |
| `◇ MODEL` | Model | Probabilistic inference without independent action selection |
| `✦ AGENT` | Agent | Agentic reasoning and selection among permitted actions |
| `◉ HUMAN` | Human | Human judgment, approval, or manual work |
| *(no glyph)* | Passive system | Queues, apps, stores, and APIs that do not choose work |

```svg
<!-- Type tag with glyph — replaces the bare tag chip from SKILL.md §6 -->
<rect x="X+8" y="Y+6" width="44" height="12" rx="2" fill="transparent" stroke="STROKE@0.40" stroke-width="0.8"/>
<text x="X+30" y="Y+15" fill="STROKE@0.8" font-size="7" font-family="'Geist Mono', monospace"
      text-anchor="middle" letter-spacing="0.08em">⚙ RPA</text>
```

The glyph is part of the tag text, not a separate icon. Widen the chip to fit (`40–52px`); everything else in the §6 node pattern is unchanged. One diagram never needs a legend entry per glyph — the legend names the classes once (`⚙ robot · ◆ workflow · ◇ model · ✦ agent · ◉ human`).

**Where the glyph is dropped.** Two cases, both deliberate:

- **Workflow diagrams** use the bare activity tags above. Every box is already a step performed by *something*, so the class is carried by the tag word itself, and the chip has no room for a glyph — in the process-detail flavor two chips (step ID and activity tag) share one 104px box edge. Where a class distinction still needs signalling, use the accent (the agent step or the human gate is the focal element).
- **Parametric types with their own chip geometry** — data flow defines an 18×10 three-letter role chip (`type-data-flow.md` §2.4) that cannot hold a glyph. There, carry the class on the **lane label** instead (`◉ BUSINESS USERS`, `⚙ RPA ROBOTS`), which is what patterns 9 and 11 require.

A diagram uses one of these conventions throughout — never glyphed tags on some nodes and bare tags on others.

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

## Application vocabulary — screens, entities, operations

The **Application card** pattern ([semantic-patterns.md §20](semantic-patterns.md)) documents apps with the same grammar agents use — `IN`/`OUT` nodes, gates, and containers come from Agent anatomy above. Three additions:

- **App chips.** The app node carries `APP` plus a platform-class chip (`WEB`, `MOBILE`, `DESKTOP`). Screens carry `SCREEN` or `MODAL` plus a **state-ID chip** (`2.1`) that the screen-states figure, the screen contract, and any prose all reference — one numbering, many pages. Data nodes use `ENTITY`; triggered work uses `FLOW`, `RPA`, `API`, `QUEUE` as elsewhere; runtime tiers use `NET`, `CACHE`, `DB`, `OBJ`, `DWH`, `BI`.
- **Logical operations.** Contracts name operations `VerbNoun` — `GetInvoice`, `SaveInvoice`, `ApproveInvoice` — never the physical implementation. The document's implementation profile maps each operation to a cloud flow, UiPath process, API route, or server action; the diagram stays conceptual.
- **Event labels and responses.** UI events label trigger edges (`ON LOAD`, `ON SAVE`, `ON APPROVE`); every async trigger has a response edge back to the screen (`ACK QUEUED`, dashed). The queue node is the visible sync–async boundary: the screen's immediate outcome is *queued*, never the downstream result.

## Edge kinds

Automation diagrams reuse the arrow grammar from SKILL.md §6; the edge kind picks the style and the label text (≤14 chars, all-caps).

| Edge kind | Label examples | Style |
|---|---|---|
| Event / trigger | `EMAIL IN`, `SCHEDULE`, `WEBHOOK` | Default muted |
| Enqueue / dequeue | `ENQUEUE`, `NEXT ITEM` | Default muted |
| UI automation | `UI STEPS`, `TYPE+CLICK` | Default muted |
| API / HTTP call | `POST /invoice`, `API CALL` | Link-blue |
| Tool call (agent → tool) | `TOOL CALL`, `INVOKE` | Link-blue |
| Reasoning / decision | `DECIDE`, `PLAN` | Accent (only if focal) |
| Approval request / response | `REQUEST OK?`, `APPROVED` | Dashed muted (suspension) |
| Exception / escalation | `SYS EXC`, `ESCALATE` | Dashed muted; accent only when the failure path is the story |
| Retry | `RETRY ×3` | Dashed muted |

The focal rule holds: accent on 1–2 elements per diagram. In most automation figures the focal element is the decision point or the human gate — not the robot.

## Automation boundaries

Most RPA/agent diagrams silently imply that everything can reach everything. Boundaries make reach explicit. Draw each as a labeled container using the **Security / Boundary** treatment (`accent @ 0.05` fill, `accent @ 0.50` dashed stroke), with the boundary name as the container's eyebrow label.

| Boundary | What it separates | Typical question it answers |
|---|---|---|
| **Network boundary** | Enterprise network vs. external services (LLM APIs, SaaS) | "Does invoice data leave our network?" |
| **Credential boundary** | Who can read which secrets | "Does the agent hold SAP credentials, or only the robot?" |
| **Approval boundary** | What may not proceed without a human | "Can this post to production unattended?" |
| **Agent permission boundary** | Which tools the agent may invoke | "Can the agent call any workflow, or only these three?" |

Rules:

- A connector crossing a boundary must carry a label naming the mechanism (`API`, `VPN`, `APPROVAL`).
- Never draw an agent with implicit access to a tool outside its permission boundary — if the agent can't call it, no connector.
- ≤2 boundaries per diagram; more than that is a dedicated guardrails figure (**Automation guardrails and boundaries** → Layer stack).

## Anti-patterns

| Anti-pattern | Why it fails |
|---|---|
| Vendor product names as node names | Locks the diagram to one stack; the business role disappears |
| Robot/workflow or model/agent drawn as the same class | Erases the kind and behavior distinction the diagram exists to show |
| Credential vault drawn as a plain database | Hides the security-relevant role; use the Security / Boundary treatment |
| A queue with no producer or no consumer | A queue is a relationship, not a decoration |
| Agent connected to every system "for context" | Implies unbounded permissions; draw only permitted tool calls |
| Robot icon clip-art crowd | The badge carries the class; decorative robots add noise |
