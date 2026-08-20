# Semantic patterns

Semantic patterns describe **what a system does**; the 11 visual types describe **how information is arranged**. Choose a pattern first when behavior, state, enforcement, or risk is load-bearing, then use its nearest visual type as the layout grammar. If no pattern matches, choose a visual type directly.

Patterns 8–19 model automation behavior — RPA, AI agents, and the humans and systems around them. They cite the vendor-neutral vocabulary in [`automation-primitives.md`](automation-primitives.md); load it alongside this file whenever one of them routes.

Use one primary pattern per figure. A second pattern may supply at most one supporting primitive; if both need full treatment, split overview and detail. Labels and outcomes must remain complete in a static frame.

## Routing table

| The reader must understand… | Semantic pattern | Nearest visual type |
|---|---|---|
| Many arrivals competing for finite service capacity | **Fan-in queue / bottleneck** | Data flow |
| Repeated questions, inputs, controls, and outputs across stages | **Stage framework with semantic slots** | Process |
| A loose conversation becoming a durable structured record | **Unstructured input → structured artifact** | Data flow |
| Why two policy decisions differ and where they first diverge | **Paired policy-evaluation traces** | Flowchart |
| Which routes cross a trust boundary and which routes are blocked | **Secure paved road** | Architecture |
| Which controls apply at each enforcement surface | **Governance / control catalog** | Layer stack |
| How defenses reduce risk and what risk remains | **Compensating security layers** | Layer stack |
| How work items travel from intake to processing | **Dispatcher / queue / performer** | Data flow |
| How a robot and a person share one workstation | **Attended automation handoff** | Swimlane |
| What happens to a work item across retries and exceptions | **Transaction lifecycle with retry and exceptions** | State machine |
| Where an automation stops and waits for a person | **Human-in-the-loop approval** | Sequence |
| How documents become validated system entries | **Document processing pipeline** | Data flow |
| What an agent can reason about and which tools it may call | **Agent with tools** | Architecture |
| Who decides vs. who executes when an agent drives automation | **Agent → RPA handoff** | Sequence |
| How a supervisor distributes work across specialist agents | **Supervisor and worker agents** | Org chart |
| How an agent improves from its own run history | **Agent memory and evaluation loop** | Loop |
| What an automation is permitted to touch, and by which control | **Automation guardrails and boundaries** | Layer stack |
| The end-to-end solution as named processes with decisions and handoffs | **RPA solution blueprint** | Flowchart |
| One agent's charter, operating mode, I/O contract, grounding, tools, and escalation | **Agent card** | Architecture |

## 1. Fan-in queue / bottleneck

**Selection triggers:** Several producers converge on one reviewer, service, gate, or constrained resource; the story depends on arrival rate, queue depth, wait, capacity, or backpressure.

**Required primitives:** Distinct sources; fanned ingress; an ordered queue with visible slots and count; a capacity/service-rate label; one constrained service point; admitted and deferred/rejected outcomes. Label units (`8/hour`, `3 slots`), not just “high.”

**Complexity budget:** ≤5 sources, ≤5 queue slots, one bottleneck, two outcomes, and ≤9 primary nodes. Aggregate excess sources as a named cohort.

**Anti-patterns:** Equal-width pipeline that hides contention; arrows merged before they can be traced; capacity implied only by box size; decorative pile-up; animation that changes item order; red alone meaning overloaded.

**Static fallback:** Show the representative final queue, numeric count/capacity, bottleneck label, and both outcome paths. A still must reveal why work waits.

**Nearest visual type:** **Data flow** by default; use **Process** when service stages, rather than sources, dominate.

## 2. Stage framework with semantic slots

**Selection triggers:** A lifecycle or operating model repeats the same semantic questions across stages, commonly Question, Input, Governance, and Output. Cross-stage comparability matters more than message timing.

**Required primitives:** Ordered stage headers; a consistent slot grid; explicit empty/not-applicable slots; stage-to-stage handoff; stable slot labels; one primary output per stage. Preserve slot order in every stage.

**Complexity budget:** 3–6 stages, 3–4 slot kinds, ≤20 populated cells, ≤2 lines per cell. Split detail when a cell needs prose.

**Anti-patterns:** Each stage invents a different internal layout; slot meaning encoded by position with no labels; fake precision from dozens of cells; confusing stage order with ownership lanes; shrinking text to keep one canvas.

**Static fallback:** Render the full stage × slot matrix with handoffs and explicit `—` or `Not applicable` entries. Do not depend on staged reveal to teach the schema.

**Nearest visual type:** **Process**; use **Swimlane** only when the repeated rows represent owners rather than semantic slots.

## 3. Unstructured input → structured artifact

**Selection triggers:** Dialogue, notes, prompts, or a rambling request are elicited, normalized, and written into a durable brief, ticket, record, schema, or other structured artifact.

**Required primitives:** Source utterance(s); clarifying questions; extracted field/value pairs; a named transformation; the durable artifact boundary; provenance links from representative statements to fields; missing/unknown state.

**Complexity budget:** ≤4 exchanges, ≤6 artifact fields, one transformation, and ≤3 provenance links. Show representative content, not a transcript.

**Anti-patterns:** “AI magic” sparkle between two boxes; artifact shown as another chat bubble; fields appearing without sources; inventing certainty for missing facts; typing animation as the only readable copy.

**Static fallback:** Show a short source excerpt beside the completed labeled artifact, with at least one provenance mapping and any unknown fields visible.

**Nearest visual type:** **Data flow**; use **Process** when elicitation has several ordered gates.

## 4. Paired policy-evaluation traces

**Selection triggers:** Two otherwise similar requests reach different outcomes; the reader needs rule-by-rule `PASS`, `FAIL`, `SKIPPED`, or `NOT REACHED` state and the first divergence.

**Required primitives:** The same ordered rules on both traces; explicit status text plus symbol/shape; inputs that differ; final outcomes; a labeled first-divergence marker; a distinction between `SKIPPED` (applicable flow intentionally bypassed) and `NOT REACHED` (evaluation stopped earlier).

**Complexity budget:** Exactly 2 traces, 3–6 rules, one first divergence, ≤12 status cells, and one outcome per trace. Move rule prose to notes if labels exceed one line.

**Anti-patterns:** Comparing two independently ordered flows; green/red dots without words; treating skipped and not-reached as synonyms; highlighting every difference; continuing a denied trace as if downstream rules ran.

**Static fallback:** Show all rule states and both outcomes at once; use a persistent bracket/line and label for the first divergence.

**Nearest visual type:** **Flowchart** for ordered decision logic; use **Sequence** only when messages between actors and time are also load-bearing.

## 5. Secure paved road

**Selection triggers:** A supported architecture creates a bounded route from intake/build to deployment; trust boundaries, privileged moments, permitted ingress, forbidden ingress, and approved versus blocked deploy paths are the point.

**Required primitives:** Labeled trust boundaries; actors and identities; permitted ingress with a positive text label; forbidden ingress terminating at the boundary; approved deployment path; blocked bypass path; privileged gate; isolated runtime; audit destination. Use different line styles and stop symbols in addition to color.

**Complexity budget:** ≤3 trust zones, ≤8 components, ≤10 paths, ≤2 forbidden paths, and one privileged gate. Split control detail into a catalog figure.

**Anti-patterns:** Dashed box called “security” with no route semantics; forbidden arrow crossing into the protected zone; secrets or identity implied but unlabeled; every component styled as trusted; a bypass path that visually rejoins the approved route.

**Static fallback:** Render every boundary and both permitted/forbidden routes. Blocked paths must visibly stop before entry or deployment.

**Nearest visual type:** **Architecture**.

## 6. Governance / control catalog

**Selection triggers:** A control inventory must be understood by where it is enforced: authoring, workspace, merge/CI, deploy/runtime, or another named surface. A single checklist would hide those enforcement points.

**Required primitives:** Enforcement-surface groups; named controls; enforcement actor (`code`, `platform`, `human`); timing (`write`, `merge`, `deploy`, `run`); bypassability or exception route; coverage/gap notation.

**Complexity budget:** 3–5 surfaces, 3–7 controls per surface, ≤24 controls total, and ≤3 attributes per control. Summarize counts only when the item list exists elsewhere.

**Anti-patterns:** 35 tiny pills; grouping by vague themes instead of enforcement point; mixing aspirations with enforced controls; icons without control names; claiming defense-in-depth without showing surface coverage.

**Static fallback:** Show the complete grouped catalog with surface headers and text labels for actor and enforcement timing; preserve gaps and exceptions.

**Nearest visual type:** **Layer stack**; use **Swimlane** when per-role responsibilities, not enforcement surfaces, are the dominant comparison.

## 7. Compensating security layers

**Selection triggers:** No layer is perfect; each defense covers a failure left by the previous layer, and residual risk must visibly narrow, transfer, or remain through the stack.

**Required primitives:** Ordered threat/risk input; named defensive layers; each layer's mitigation; explicit limitation or escape; residual-risk carrier between layers; final residual risk and consequence/response. Use labels or decreasing measures, never area alone.

**Complexity budget:** 3–5 layers, one primary risk thread, ≤2 mitigations per layer, and one final residual-risk statement. Split multiple unrelated threats into separate figures.

**Anti-patterns:** Implying the final layer makes risk zero; equal opaque slabs with no propagation; treating audit as prevention; shrinking shapes without numeric or verbal meaning; reversing prevention/detection/recovery order without explanation.

**Static fallback:** Show the complete propagation chain: initial risk → mitigation → escaped risk at every layer → final residual risk and response.

**Nearest visual type:** **Layer stack**; use **Architecture** with labeled boundary containers when containment, rather than ordered compensation, carries the meaning.

## 8. Dispatcher / queue / performer

**Selection triggers:** Work items are produced by one process (dispatcher) and consumed by another (performer) through a queue; throughput, transaction state, and decoupling are the point. The canonical unattended RPA topology.

**Required primitives:** Trigger; dispatcher (⚙ RPA); queue with visible item count; orchestrator assigning work; one or more performers (⚙ RPA); target business app; success and exception outcomes. Label the queue with units (`126 pending`), not adjectives.

**Complexity budget:** 1 dispatcher, 1 queue, ≤2 performers, ≤2 outcome paths, ≤9 primary nodes. Aggregate parallel performers as one node with a `×N` sublabel.

**Anti-patterns:** Dispatcher wired straight to performer with the queue as decoration; queue drawn as a plain arrow; orchestrator omitted so robots appear self-starting; exception path missing so the diagram implies 100% success.

**Static fallback:** Show the queue with its count, both the enqueue and dequeue edges, and both outcome paths in one frame.

**Nearest visual type:** **Data flow**; use **Sequence** when the assignment protocol between orchestrator and robot is the story.

## 9. Attended automation handoff

**Selection triggers:** A robot and a person share one workstation or session, taking turns — the robot prepares, the human judges, the robot completes. Who holds control at each moment is the point.

**Required primitives:** One lane per actor (◉ HUMAN, ⚙ RPA, plus the business app); explicit handoff edges with what is passed; the moment of control transfer; the human's judgment step named as a decision, not a click.

**Complexity budget:** ≤3 lanes, ≤8 steps, ≤3 handoffs. More actors means the process is not attended automation — re-route.

**Anti-patterns:** Human lane reduced to `clicks OK`; robot steps and human steps styled identically; handoff drawn without stating what crosses (screen, data, control); background robot work hidden so the human appears idle.

**Static fallback:** Every handoff labeled with its payload and direction; the frame must show who is in control at each step without animation.

**Nearest visual type:** **Swimlane**.

## 10. Transaction lifecycle with retry and exceptions

**Selection triggers:** A work item moves through states — new, in progress, succeeded, failed — with retry rules and the business/system exception distinction. Operational behavior under failure is the point.

**Required primitives:** Named states; transitions with guards (`retry < 3`); a **business exception** path (bad data — do not retry) distinct from a **system exception** path (environment failure — retry); a terminal abandoned/DLQ state; retry counter.

**Complexity budget:** ≤6 states, ≤10 transitions, exactly 2 exception classes, 1 retry rule. More states means two lifecycles are mixed — split.

**Anti-patterns:** One generic `FAILED` state hiding the business/system distinction; retry drawn as a self-loop with no limit; abandoned items falling off the diagram with no terminal state; guards implied by color alone.

**Static fallback:** All states, both exception classes, and the retry guard visible with text labels in one frame.

**Nearest visual type:** **State machine**.

## 11. Human-in-the-loop approval

**Selection triggers:** An automation suspends, requests a person's validation or approval, and resumes or aborts on the response. The suspension — who waits, on what, for how long — is the point.

**Required primitives:** Automation actor (⚙ RPA or ✦ AGENT); approval surface (task inbox, form); approver (◉ HUMAN) with their business role; the suspension interval made visible; approve and reject continuations both drawn; timeout/escalation rule if one exists.

**Complexity budget:** ≤5 lifelines, 1 approval gate (a second gate splits the figure), 2 continuations, ≤1 timeout rule.

**Anti-patterns:** Approval drawn as an instant synchronous call; the reject path missing; the approver anonymous (`User`) instead of a role; the suspended state invisible so the process looks continuous.

**Static fallback:** The suspension interval, the request content, and both continuations readable in one frame.

**Nearest visual type:** **Sequence**; use **Process** when several approval steps form a chain and timing is secondary.

## 12. Document processing pipeline

**Selection triggers:** Documents arrive, are classified, have fields extracted, pass or fail validation, and post into a business system — with a human correction path for low-confidence results.

**Required primitives:** Document source; classification step; extraction step with named fields; confidence gate with threshold (`< 85% → review`); human validation lane (◉ HUMAN); posting step into the target app; rejected/unprocessable outcome.

**Complexity budget:** ≤6 pipeline stages, 1 confidence gate, ≤6 named fields, 2 outcomes. Representative fields, not the full schema.

**Anti-patterns:** `AI magic` box between document and data; confidence gate without a number; human review drawn as an exception instead of a designed path; extracted fields appearing with no source document link.

**Static fallback:** One document's journey with the gate threshold, one field example, and both outcomes visible.

**Nearest visual type:** **Data flow**; use **Swimlane** when the human/robot division of labor dominates.

## 13. Agent with tools

**Selection triggers:** An LLM agent reasons over a goal and acts through a bounded set of tools — functions, MCP servers, APIs, RPA workflows. What the agent can reach, and what it cannot, is the point.

**Required primitives:** Agent (✦ AGENT) with its **operating-mode chip** (`AUTO`/`CONV`/`STEP`) and charter in the sublabel, plus a one-line I/O contract (`in: … → out: …`); LLM; named tools with type tags; the permission boundary around the permitted toolset; data stores the agent reads — drawn as dashed `RETRIEVE` grounding edges, visually distinct from link-blue tool calls, grouped in a grounding container when there are ≥2 sources ([automation-primitives.md § Agent anatomy](automation-primitives.md)); the human or system that receives the result.

**Complexity budget:** 1 agent, ≤5 tools, ≤2 stores, ≤2 boundaries, ≤9 primary nodes. A second agent re-routes to **Supervisor and worker agents**.

**Anti-patterns:** Agent connected to everything `for context`; tools and knowledge stores styled identically; the LLM omitted so the agent looks self-contained; boundary drawn but with connectors crossing it unlabeled.

**Static fallback:** Every permitted tool edge labeled; anything outside the boundary visibly unreachable.

**Nearest visual type:** **Architecture**.

## 14. Agent → RPA handoff

**Selection triggers:** An agent interprets a request, decides which deterministic capability applies, and delegates execution to an RPA workflow, API, or function — then handles the result or failure. Decide vs. execute is the point.

**Required primitives:** Requester; agent (✦ AGENT) with an explicit decision step; the selected deterministic capability (⚙ RPA) with the unselected alternatives implied by a selection label; execution against the business system; result returning to the agent; failure path where the agent analyzes and escalates to a human.

**Complexity budget:** ≤5 lifelines, 1 decision point, 1 executed capability, 1 failure/escalation path.

**Anti-patterns:** Agent drawn performing the UI steps itself; decision step hidden so the handoff looks hardcoded; failure path ending at the robot instead of returning to the agent; escalation to an anonymous inbox.

**Static fallback:** The decision label, the delegation edge, and the full failure path readable without motion.

**Nearest visual type:** **Sequence**; use **Process** when the pipeline shape matters more than message timing.

## 15. Supervisor and worker agents

**Selection triggers:** A supervisor agent decomposes work and routes it to specialist workers (agents, robots, or humans), owns aggregation, and owns escalation. Who is responsible for what, and where failures go, is the point.

**Required primitives:** Supervisor (✦ AGENT) at the root; workers with class badges (✦/⚙/◉); routing criteria on edges; aggregation of results; the escalation edge to a human owner; each worker's specialty in its sublabel.

**Complexity budget:** 1 supervisor, ≤5 workers, depth ≤3, 1 escalation owner. Deeper hierarchies split into per-team figures.

**Anti-patterns:** Workers drawn as interchangeable clones with no specialty; routing edges unlabeled so distribution looks random; escalation missing so the tree implies full autonomy; supervisor doing work items itself.

**Static fallback:** All routing criteria and the escalation path visible as text in one frame.

**Nearest visual type:** **Org chart**; use **Architecture** when workers share infrastructure and the topology matters more than the hierarchy.

## 16. Agent memory and evaluation loop

**Selection triggers:** An agent acts, observes outcomes, writes to memory or an evaluation store, and its next action improves — a reinforcing cycle where the accumulated store is the hub.

**Required primitives:** Ordered loop steps (act → observe → evaluate → update); a central memory/evaluation hub that every cycle enriches; what flows into the hub and what flows out; the trigger for each new cycle; a quality signal that visibly changes across cycles.

**Complexity budget:** ≤6 loop steps, 1 hub, ≤2 external inputs. One loop per figure.

**Anti-patterns:** A circle of arrows with no hub, so nothing accumulates; `learns` as a label with no mechanism; evaluation and memory conflated into one box when the pattern needs both; improvement claimed but no signal shown.

**Static fallback:** The full cycle with the hub's contents named; the improvement signal stated in text (`accuracy 71% → 89%`), not implied by motion.

**Nearest visual type:** **Loop**.

## 17. Automation guardrails and boundaries

**Selection triggers:** The reader must trust what an automation may and may not do: which credentials it holds, which systems it may touch, which actions demand approval, where its permissions end.

**Required primitives:** Named control surfaces as layers (identity, credentials, tool permissions, approval gates, audit); at each layer the enforced control and its enforcement actor (`platform`, `code`, `human`); the request path crossing the layers; at least one visibly blocked action; the audit destination.

**Complexity budget:** 3–5 layers, ≤3 controls per layer, 1 permitted path, ≥1 blocked action. Full control inventories re-route to **Governance / control catalog**.

**Anti-patterns:** Guardrails listed beside the diagram instead of on the path; every layer green so nothing is visibly forbidden; approval and audit conflated; the agent's own judgment drawn as a control layer.

**Static fallback:** The permitted path, every enforcement actor, and the blocked action readable in one frame.

**Nearest visual type:** **Layer stack**; use **Architecture** when the boundaries are spatial (network, credential zones) rather than stacked controls.

## 18. RPA solution blueprint

**Selection triggers:** The reader needs the automation as its solution-design artifact — either the whole solution as named processes on one canvas (multi-process blueprint), or one numbered process at PDD-writing depth: step IDs, technical annotations, and the workflow logic including agent steps (process detail).

**Required primitives:** *Blueprint flavor:* named phase bands with dashed dividers; one queue bridge at the producing phase's edge. *Process-detail flavor:* numbered title, step-ID chips, under-box technical annotations (schedule, endpoint, entity, threshold), agent step with confidence gate falling back to human review. *Both:* one Start; activities with system-class tags (`MAIL`, `DOC AI`, `AGENT`, `HUMAN`, `APP` — vendor names in sublabels only); decisions with every exit labeled; human branch that merges back or reaches an End; terminal End(s) including the reject path.

**Complexity budget:** Blueprint: ≤3 phases, ≤5 activities per phase, ≤3 decisions, 1 queue bridge — extended on `print-a3-landscape` per the escalation ladder in [type-flowchart.md](type-flowchart.md), which owns the numbers. Process detail: 1 process, ≤8 activities, ≤3 decisions, ≤6 annotations. Phase banding (or the single numbered process) is the sanctioned zoning above the 9-node target; above that, split into a detail set (type-flowchart.md § Detail set).

**Anti-patterns:** Vendor product names as node tags; a reject path that silently disappears instead of reaching an End; the queue drawn as an arrow or cylinder; every decision accented; phases implied by whitespace with no divider or label; implementation detail crammed inside the box instead of annotated under it.

**Static fallback:** The full flow with all branch labels, step IDs, annotations, and both terminal outcomes readable in one frame.

**Nearest visual type:** **Flowchart** (phased blueprint variant); use **Data flow** when role lanes matter more than workflow logic, or **Sequence** for the runtime message view of one transaction.

## 19. Agent card

**Selection triggers:** One agent must be documented as its architecture artifact — charter, operating mode, I/O contract, what it reads, what it may do, and where a human takes over. The client-facing solution annex for an agent built on any platform (UiPath, Copilot Studio, LangGraph, plain code — the vendor lexicon in [automation-primitives.md](automation-primitives.md) maps the terms).

**Required primitives:** Page-context panel (`AGENT CARD` eyebrow; `CHARTER`, `MODE`, `GUARDRAILS` lines); the **I/O spine** — IN node → agent (✦ AGENT + operating-mode chip) → OUT node, ink strokes, payload labels (`EVENT`/`QUERY` → `RESULT`/`ANSWER`); LLM node with a `PROMPT` edge; **grounding container** with ≥1 source and dashed `RETRIEVE` edges in; **tool-permission boundary** with ≥1 tool and link-blue `TOOL CALL` edges out; ≤2 dashed-accent escalation edges to named human roles, each labeled with its condition; on-edge guardrail gates where a control bites. The fixed spatial grammar carries the meaning: *horizontal = data flow; lower-left = knowledge; lower-right = action; top = reasoning; bottom = the human.*

**Conversational variant:** `CONV` chip; IN is the user's query (per turn), OUT the answer (+ source); escalation reads "human takes over the session"; the `MODE` panel line says turn-based. When turn timing or session dynamics are the story, draw that figure as a **Sequence directly** — reach for **Human-in-the-loop approval** only when a suspension or handoff is the story. The card stays the static architecture view.

**Complexity budget:** 1 agent, ≤4 grounding sources, ≤5 tools, ≤2 escalation targets, ≤2 guardrail gates, 2 containers, **≤14 primary nodes total** (IN, OUT, LLM, and each human count; containers and gates don't). The two containers are the card's sanctioned zoning above the nine-node target — the same mechanism as the blueprint's phase banding — and the ceiling is absolute: category maxima are non-composable — the 14-node total always wins (4 sources + 5 tools forces dropping a human or gate-owner node). A busier agent splits its inventory into a linked Agent-with-tools or guardrails figure rather than growing the card.

**Anti-patterns:** An escalation or guardrails *container*; grounding invisible so answers look like magic; grounding sources styled as tools; vendor product names in chips; a second accent (the agent is focal; the escalation edge may share the accent as its continuation); the operating-mode chip omitted so a copilot is indistinguishable from an autopilot; a `⚙`-class control drawn with the `◉` glyph (the gate glyph states the enforcing class, and ◉ means human).

**Static fallback:** The card is static by definition — panel, spine, both containers, and every edge label readable in one frame.

**Nearest visual type:** **Architecture**. As a page inside a detail set, the card is a non-flowchart annex page carrying the set's numbering and navigation ([type-flowchart.md § Detail set](type-flowchart.md)).

## Composition rules

- The semantic pattern may specialize status, boundary, queue, or propagation primitives; the selected type still owns page axis, connector grammar, spacing, and type-specific limits.
- Apply the stricter of the pattern budget and visual-type budget. Semantic cells/statuses are not permission to exceed the nine-node overview target.
- Use stable text for states and outcomes. Color, motion, and position reinforce meaning but never carry it alone.
- Optional animation is a presentation layer, not another pattern. Load [`animation.md`](animation.md) only when motion is requested or materially clarifies ordered change.
