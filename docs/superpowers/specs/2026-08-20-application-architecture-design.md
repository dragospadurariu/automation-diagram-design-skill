# Application architecture family: application card, screen contract, screen states, runtime topology

**Status:** approved in chat (mockups iterated through 3 external-review rounds, 2026-08-20)
**Date:** 2026-08-20
**Scope:** one new semantic pattern (**Application card** → Architecture, 19→20), an application vocabulary block in `automation-primitives.md`, a **screen-states flavor** in `type-state.md`, a conditional **runtime-deployment-topology** note in `type-architecture.md`, a generalized annex-page rule in `type-flowchart.md`, four example assets + gallery tabs, README refresh with screenshots (including the agent-card ones missed in 0.3.0), ADR 0002 amendment, minor version bump (0.3.0 → 0.4.0). No new visual type, no new color role, no emitter/import changes.

## 1. Context

Users document applications (UiPath Apps, Power Apps, Next.js, anything) alongside RPA and agents. Three external-review rounds on working mockups (`experiments/app-mockups/`, gitignored) converged on a **family of pages with explicit selection conditions and information ownership** — the reviewer's closing rule is binding: *these are defaults with selection conditions, never mandatory pages.*

| Page | Question it answers | Condition to draw it | Canonical owner of |
|---|---|---|---|
| **App card** | who uses it, what data it touches, what it triggers | standard for any documented app | users/roles, identity, aggregated entities & automations |
| **Screen states** | which screen is the user in; what event moves them | only when ≥2 states with meaningful navigation | navigation, events, guards |
| **Screen contract** | one screen's operations, responses, authorization | only for architecturally significant screens | reads/writes, commands, immediate responses, authorization |
| **Runtime deployment topology** | what it runs on, in which layers, who operates it | only when deployment, integration, residency, scaling, or operational ownership materially affects the solution | tiers, ownership, environments, HA |
| **Sequence** (existing patterns) | timing, callback, retry, failure of one interaction | runtime deep-dive | chronology, retries, timeouts, error paths |

The ownership column is the **anti-drift rule**: a fact appears canonically on one page; other pages may reference but never restate it differently (the review caught exactly such a drift between two mockups).

## 2. Decision

### 2.1 New semantic pattern 20: **Application card** → Architecture

One pattern with a main view and a conditional drill-down — not three patterns.

**Selection triggers:** An application must be documented as its functional-context artifact: purpose, users and roles, the data it reads/writes, the identity gate, and the automations/side effects it triggers — on any platform (the card is the *functional* view; the technical view is the conditional annex below).

**Main view (app card) — required primitives:** Page-context panel (`APP CARD · FUNCTIONAL VIEW` eyebrow; `PURPOSE`, `USERS` + roles, `SCREENS · N + M modals`, `PROFILE · <implementation>` lines — one implementation profile chosen per final document; the card itself stays platform-neutral); the user spine — `◉ USERS` node → app (focal, `APP` + platform-class chip) → OUT node naming the **decision/outcome event**, never the entity (`Invoice approved · decision event`, not "the invoice"); identity provider above with an automated `SSO` gate on the user edge; **DATA container** below-left (entities with `RW · system of record` / `read only` sublabels; READ dashed, WRITE solid ink — the write always lands on the RW entity); **AUTOMATIONS · BY EVENT boundary** below-right (link-blue `COMMAND` edges; outcomes are `queued`, not completed).

**Drill-down variant (screen contract)** — one page per **architecturally significant screen only**. A screen qualifies when it has at least one of: writes data; triggers a flow/RPA/API; crosses a sync–async boundary; carries authorization or business thresholds; needs audit, retry, or error handling; combines multiple data sources. Read-only list screens stay in screen states only. Required primitives: panel (`SCREEN CONTRACT · <id>`; `REACHED FROM` matching the screen-states IDs; `OPERATIONS` as **logical operation names** — `GetInvoice`, `SaveInvoice`, `ApproveInvoice` — the profile decides the physical form; `GUARDRAILS` naming the enforcement layer; `AUDIT` as a link, not a claim); the screen focal with its state-ID chip; `DATA · FOR THE SCREEN` container (reads dashed, sync writes solid); `TRIGGERED OPERATIONS` boundary with the async queue visible and the **response edges back to the screen** (`ACK QUEUED` dashed) — a contract without responses is half a contract; automated auth gates (`⚙ ROLE + AMOUNT`) on the governed edge.

**Budget:** app card ≤12 primary nodes, 2 containers. Screen contract: 1 screen, ≤3 data dependencies, ≤3 events, ≤2 downstream steps, exactly 1 async boundary — past that, the downstream moves to a Sequence figure. Category maxima are non-composable; the total always wins.

**Anti-patterns:** a mandatory page per screen; outcome and entity conflated on the spine; a screen "posting to ERP" (it enqueues a command; the result is queued); guardrails only in the panel with no gate on the governed edge; physical implementations (`Power Automate flow`) as node names where a logical operation belongs; the same behavior stated differently on two pages (ownership table above).

**Static fallback:** everything readable in one frame; both cards are static by definition.

**Nearest visual type:** **Architecture**. As detail-set pages, all family pages are annex pages (§2.4).

### 2.2 Screen-states flavor (`type-state.md`)

A flavor of the existing State machine type, no new pattern: screens are states, UI events are transitions, roles are guards — the existing `event [guard] / action` notation. Conventions: initial dot = post-sign-in entry (the IdP's hosted sign-in is not a state of the app); `SCREEN` / `MODAL` tags with **state-ID chips** (`2.0`, `2.1`) that other pages reference; modals drawn with the transient (dashed Optional/Async) treatment; every state reachable *and leavable* — returns explicit (`CANCEL`, `BACK`), async acknowledgements as their own transitions (`CONFIRM [AUTH] / ENQUEUE` then `ACK QUEUED →` target; failure stays); data bindings as state sublabels. Budget: the type's existing ≤6 states / ≤10 transitions. Drawn only when the app has ≥2 meaningfully connected states.

### 2.3 Runtime deployment topology (conditional annex, `type-architecture.md` note)

The layered technical view (the classic web-architecture picture) drawn with the **existing Architecture type**: ≤3 layer zones (`EDGE / APPLICATION / DATA`), the browser/client as an **external node above the zones** (the 3-zone rule stands — verified against the type's own limit), a `DEPLOYMENT` context panel (`MODEL`, `OWNERSHIP`, `ENVIRONMENTS`, `REGION · HA`) so `×N` means something auditable. **Conditional, not pro-code-only:** drawn when deployment, integration, network, residency, scaling, or operational ownership materially affects the solution — a Power Platform profile fills it with environments/connectors/gateways; an IaaS profile with LB/VMs/DBs. Compression is declared: collapsed services carry `(collapsed)` sublabels and the fidelity ledger names them.

### 2.4 Annex rule generalized (`type-flowchart.md`)

The detail-set annex sentence generalizes from "the first is the agent card" to: annex pages may use **any existing visual type** — agent card and app card / screen contract (Architecture), screen states (State machine), runtime topology (Architecture) — all carrying the set's numbering, colophon, navigation, and `--set` verification.

### 2.5 Application vocabulary (`automation-primitives.md`)

A compact block after Agent anatomy: **App node chips** (`APP` + platform-class `WEB`/`MOBILE`/`DESKTOP`; `SCREEN`/`MODAL` with state-ID chips; `ENTITY`; `FLOW`; `NET`, `CACHE`, `DB`, `OBJ`, `DWH`, `BI` for topology tiers); **logical operations** naming convention (`VerbNoun` — `GetInvoice`, `ApproveInvoice`; the implementation profile maps them to flows/processes/routes/actions); **event labels** (`ON LOAD`, `ON SAVE`, `ON APPROVE`; responses `ACK QUEUED`); the reminder that `IN`/`OUT`, gates, and containers come from Agent anatomy — one grammar across agents and apps.

## 3. Files touched

- `references/semantic-patterns.md` — §20 + routing row + intro 8–19 → 8–20.
- `references/automation-primitives.md` — Application vocabulary block; rows 8–19 → 8–20 mention.
- `references/type-state.md` — screen-states flavor + example entry.
- `references/type-architecture.md` — runtime-topology conditional-annex note + example entries (app card, screen contract, runtime topology).
- `references/type-flowchart.md` — generalized annex sentence.
- `SKILL.md` — routing row (`An application's users, data, screens, and triggered automations` → **Application card** → Architecture) + description hooks (`application and screen diagrams — app cards, screen flows and contracts, runtime deployment topology`), mirrored verbatim in the 3 manifest description slots.
- `scripts/verify-semantic-motion.py` — `PATTERN_NAMES` + `"Application card"`, OK string 19 → 20, same commit as the ADR 0002 amendment.
- Assets (hardened from the reviewed mockups, slugs = file stems): `example-app-card.html`, `example-screen-states.html`, `example-screen-contract.html`, `example-runtime-topology.html` + 4 `data-single` gallery tabs (13i–13l).
- **README.md** — fix stale counts (patterns 18 → 20, automation patterns 11 → 13); new section for the application family with screenshots; add the agent-card screenshots missed in 0.3.0. New `docs/screenshots/`: `agent-card.png`, `agent-card-conversational.png`, `app-card.png`, `screen-states.png`, `screen-contract.png`, `runtime-topology.png` (Playwright, @2, diagram `<svg>` only, same as existing screenshots).
- ADR 0002 amendment (count 20); `bump-plugin-version.py --minor` → 0.4.0.

## 4. Non-goals

No new visual type; no data-model/ER annex (ER was cut in ADR 0007 — a future decision if relations must be drawn); no drawio round-trip; no emitter/import changes; no new color role.

## 5. Verification

Full existing gate suite; new assets pass self_check, verify-geometry, lint-skin (fix the known ETL-label overlap from the mockup during hardening); pattern/type counters move per ADR procedure; README image paths must exist (manual check — docs-sync does not cover images).
