# Automation primitives

The shared vocabulary for every automation diagram. Semantic patterns (rows 8–18 of the routing table) cite these primitives by name; this file defines what each one means, how it is drawn, and how edges between them are styled. Load it whenever an automation pattern routes.

**Vendor-neutral by design.** The internal concept is `Queue`, never `UiPath Orchestrator Queue`. Platform names (UiPath, Power Automate, Automation Anywhere, LangGraph, …) belong in the technical **sublabel** (Geist Mono), never in the node name or the type tag. This keeps one diagram language across every client stack.

## Node primitives

Each primitive maps to a node treatment from the design system (SKILL.md §5) plus a type tag. The tag is the rectangular chip in the node's top-left corner (Geist Mono, 7px, uppercase).

| Primitive | Type tag | Meaning | Node treatment |
|---|---|---|---|
| **Human** | `HUMAN` | Operator, approver, or business user performing manual steps | Input / User |
| **RPA Robot** | `RPA` | Deterministic execution — scripted UI or API steps, attended or unattended | Backend / API / Step |
| **Agent** | `AGENT` | LLM-driven component that reasons and decides | Backend / API / Step (focal when the decision is the story) |
| **Orchestrator** | `ORCH` | Scheduler / control plane that assigns work to robots or agents | Backend / API / Step |
| **Queue** | `QUEUE` | Ordered work items / transactions awaiting a consumer | Store / State |
| **Trigger** | `TRIG` | What starts the automation — schedule, event, email, webhook, API | Input / User |
| **Business App** | `APP` | Target system — ERP, CRM, browser app, legacy desktop | External / Cloud |
| **API** | `API` | Programmatic integration point | Backend / API / Step |
| **Tool** | `TOOL` | Capability exposed to an agent — function, MCP server, RPA workflow | Backend / API / Step |
| **LLM** | `LLM` | The model an agent calls for reasoning | External / Cloud |
| **Memory** | `MEM` | Agent short/long-term memory | Store / State |
| **Knowledge Base** | `KB` | RAG / document store the agent retrieves from | Store / State |
| **Human Approval** | `APPROVAL` | Suspension point where a person validates, approves, or rejects | Input / User (focal when the gate is the story) |
| **Credential Vault** | `VAULT` | Secrets store — never drawn as a plain data store | Security / Boundary |
| **Document** | `DOC` | Payload artifact — PDF, email, spreadsheet, image | Store / State |
| **Audit / Logs** | `AUDIT` | Telemetry, run history, evidence trail | Store / State |
| **Exception** | `EXC` | Business or system exception outcome | Optional / Async (dashed) |
| **Retry / DLQ** | `RETRY` | Recovery mechanism — retry policy, dead-letter queue | Optional / Async (dashed) |

Naming: the node name states the business role (`Invoice Performer`, `Exception Analyst`, `Finance Approver`); the sublabel states the technical detail (`unattended`, `gpt · tool-enabled`, `SAP FI`).

## Activity tags — who executes this step

The table above types **actors and stores** in a topology diagram, where a node *is* a robot, a queue, an agent. A workflow diagram (flowchart, process, swimlane) is different: every box is a *step*, and the tag answers "which system performs it". That is a closed set, and it maps onto the primitives above:

| Activity tag | Step is performed by | Maps to primitive |
|---|---|---|
| `MAIL` | A mailbox or mail connector — read, send, save attachments | Trigger / Business App |
| `DOC AI` | A document-understanding model — digitize, classify, extract | Business App (model service) |
| `AGENT` | An LLM agent reasoning over the step | Agent |
| `HUMAN` | A person — validate, approve, correct, handle an exception | Human / Human Approval |
| `RPA` | A robot executing scripted UI or API steps | RPA Robot |
| `API` | A direct programmatic call | API |
| `APP` | A business application being written to or read from | Business App |
| `QUEUE` | A queue being produced to or consumed from | Queue |

Same vendor-neutral rule: `DOC AI`, never `Document Understanding`; `HUMAN`, never `Action Center`. The product name goes in the sublabel or the annotation. Do not invent a tag outside this set — pick the closest one and let the sublabel carry the specificity.

## Badge convention — deterministic vs. agentic vs. human

The reader must tell at a glance whether a box acts by script, by reasoning, or by hand. **In topology diagrams** (architecture, data flow, org chart — where the node is the actor) the tag carries a glyph prefix:

| Glyph + tag | Class | Behavior the reader may assume |
|---|---|---|
| `⚙ RPA` | Deterministic | Same input, same steps, same output — predictable, auditable |
| `✦ AGENT` | Agentic | Chooses among actions; output depends on reasoning |
| `◉ HUMAN` | Human | Judgment, approval, manual work |
| *(no glyph)* | System | Queues, apps, stores, APIs — passive infrastructure |

```svg
<!-- Type tag with glyph — replaces the bare tag chip from SKILL.md §6 -->
<rect x="X+8" y="Y+6" width="44" height="12" rx="2" fill="transparent" stroke="STROKE@0.40" stroke-width="0.8"/>
<text x="X+30" y="Y+15" fill="STROKE@0.8" font-size="7" font-family="'Geist Mono', monospace"
      text-anchor="middle" letter-spacing="0.08em">⚙ RPA</text>
```

The glyph is part of the tag text, not a separate icon. Widen the chip to fit (`40–48px`); everything else in the §6 node pattern is unchanged. One diagram never needs a legend entry per glyph — the legend names the classes once (`⚙ deterministic · ✦ agentic · ◉ human`).

**Where the glyph is dropped.** Two cases, both deliberate:

- **Workflow diagrams** use the bare activity tags above. Every box is already a step performed by *something*, so the class is carried by the tag word itself, and the chip has no room for a glyph — in the process-detail flavor two chips (step ID and activity tag) share one 104px box edge. Where a class distinction still needs signalling, use the accent (the agent step or the human gate is the focal element).
- **Parametric types with their own chip geometry** — data flow defines an 18×10 three-letter role chip (`type-data-flow.md` §2.4) that cannot hold a glyph. There, carry the class on the **lane label** instead (`◉ BUSINESS USERS`, `⚙ RPA ROBOTS`), which is what patterns 9 and 11 require.

A diagram uses one of these conventions throughout — never glyphed tags on some nodes and bare tags on others.

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
| Agent and robot drawn identically | Erases the deterministic/agentic distinction the diagram exists to show |
| Credential vault drawn as a plain database | Hides the security-relevant role; use the Security / Boundary treatment |
| A queue with no producer or no consumer | A queue is a relationship, not a decoration |
| Agent connected to every system "for context" | Implies unbounded permissions; draw only permitted tool calls |
| Robot icon clip-art crowd | The badge carries the class; decorative robots add noise |
