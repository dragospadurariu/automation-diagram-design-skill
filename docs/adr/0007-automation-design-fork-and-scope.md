# ADR 0007 — Automation-design fork: scope, vocabulary, and the 11-type cut

**Status:** accepted (v0.1)

## Context

This repository is a hard fork of [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design) v2.5.0 (MIT), repositioned as **Automation Design** — architecture diagrams for RPA, AI agents, and hybrid automation systems. A generic 28-type diagram generator serves that goal poorly: the identity is diffuse, the selection guide is dominated by chart types irrelevant to automation, and the description's routing surface competes with itself.

## Decision

Three changes, made together:

1. **The visual-type taxonomy is cut from 28 to 11** — architecture, IT current-state, flowchart, sequence, state machine, swimlane, loop, org chart, layer stack, process, data flow. Chart types (bar, line, scatter, gantt, treemap, radar, pyramid, venn, quadrant, timeline), data-platform types (ER, medallion, high-level, DP integration, DP security matrix), and containment types (nested, tree) are deleted, with their examples, screenshots, and dedicated verifiers. ADR 0002's rule is unchanged: semantic patterns never add a type; the count moves only for a new layout grammar.
2. **Behavior is modeled by 18 semantic patterns** — the 7 inherited ones plus 11 automation patterns (dispatcher/queue/performer, attended handoff, transaction lifecycle, human-in-the-loop approval, document processing, agent with tools, agent→RPA handoff, supervisor/workers, agent memory loop, guardrails/boundaries, RPA solution blueprint — the last routing to flowchart). All route to the 11 kept types, per ADR 0002.
3. **A vendor-neutral vocabulary is first-class** — `references/automation-primitives.md` defines the node primitives (robot, agent, human, queue, orchestrator, …), the badge convention (`⚙ RPA` / `✦ AGENT` / `◉ HUMAN`), edge kinds, and automation boundaries. The internal concept is `Queue`, never a vendor product name; vendor packs may later map vocabulary onto specific platforms without changing the core.

Versioning restarts at 0.1.0. Upstream is not tracked; fixes are cherry-picked manually if ever needed.

## Consequences

- The counters in `verify-semantic-motion.py` and `verify-docs-sync.py` moved 28 → 11 and 7 → 18 patterns with this record, per the procedure in ADR 0002's amendment.
- Adding a diagram type back (or a new one) still requires the full §10 shipping set plus a description hook — and now also a justification against the automation scope.
- Adding automation behavior costs one pattern section plus a routing-table row, and must cite primitives from `automation-primitives.md` rather than inventing per-pattern vocabulary.
- Upstream improvements to shared machinery (geometry verification, import/export, profiles) no longer arrive automatically; that trade was accepted for freedom to restructure.
