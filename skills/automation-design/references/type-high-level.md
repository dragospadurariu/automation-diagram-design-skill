# High-level architecture

**Best for:** an end-to-end automation or data platform summarized as a fixed sequence of phases, with operational boundaries and cross-cutting controls visible at a glance.

**Not for:** an arbitrary component network. Use **Architecture** when topology and peer-to-peer relationships dominate. High-level architecture is a phase-led story: sources → ingestion → processing/storage → decision or analysis → destination.

## Required visual grammar

### Phase rail

- A top rail divides the system into 4–6 named phases.
- Use squared chevrons or adjacent bands, alternating `ink` and `muted`; labels are Geist Mono 7px uppercase.
- Every primary node aligns beneath exactly one phase.
- Phase labels describe capability, not vendor names.

### Main flow

- Read left to right with one unmistakable primary path.
- Keep the main path on a shared horizontal rhythm; vertical movement is reserved for stores, queues, or control planes.
- Default edges use `muted`; the automated/focal route may use `accent` across at most two connected segments.
- Draw connectors first, then nodes, then label masks.

### Boundaries and cross-cutting controls

- External sources sit in a dashed boundary outside the runtime platform.
- The runtime/deployment boundary uses a solid `rule-solid` outline.
- Orchestration may span the top of the runtime boundary; identity, policy, or monitoring may span the bottom.
- Dashed drops from a control plane mean trigger, policy, or observation — never primary data transfer.
- Name the execution environment only when it changes deployment understanding.

### Nodes

- Node name: Geist 11–12px/600.
- Technical sublabel: Geist Mono 8–9px.
- Optional type tag: Geist Mono 7px in an `rx=2` rectangle.
- Focal node: `accent-tint` fill, `accent` stroke; all other nodes stay neutral.
- Use platform/vendor icons only when identity materially helps recognition; the text label remains mandatory.

## Complexity budget

- 4–6 phases.
- 7–9 primary nodes, including sources summarized as a group.
- 1 runtime boundary.
- 2 cross-cutting control planes.
- 12 primary connections.
- 1 focal component or route.

If a phase needs more than two components, split it into a detail diagram and keep the high-level page as the index.

## Legend

Use a horizontal bottom strip. Include only the boundary, focal path/node, and dashed control edge when present.

## Anti-patterns

- Treating the phase rail as decoration while nodes ignore it.
- Showing every service, queue, topic, and database on the overview.
- Mixing primary data movement with orchestration triggers.
- Repeating product logos without operational meaning.
- Using multiple accents or several competing focal nodes.
- Replacing the general Architecture type with this rigid phase layout.

## Shipped examples

- `assets/example-high-level.html` — minimal light.
- `assets/example-high-level-dark.html` — minimal dark.
- `assets/example-high-level-full.html` — full editorial frame.
