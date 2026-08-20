# ADR 0002 — Semantic patterns never expand the 27-type taxonomy

**Status:** accepted (v2.3)

## Context

Auditing behavior-rich figures (queues, policy traces, trust boundaries) showed the skill could arrange boxes but not model system behavior. The obvious fix — new diagram types — would balloon the taxonomy, dilute the selection guide, and force every new behavior into a new layout grammar.

## Decision

Behavior is a separate axis. The seven semantic patterns in `references/semantic-patterns.md` each route to the **nearest existing visual type** for layout; a pattern owns semantic primitives and a tighter budget, never a second layout grammar. The visual-type count stays at 27 unless a genuinely new *layout* grammar appears.

## Consequences

- The visual-type count is a stable, verifiable claim (`verify-semantic-motion.py` and `verify-docs-sync.py` both count it) — 27 when this record was accepted; see Amendments for the current figure.
- A new behavior costs one pattern section plus a routing-table row — not a new type reference, template set, and example triple.
- If a pattern ever needs a layout no existing type provides, that is the signal to add a type, with the full §10 shipping set.

## Amendments

**2026-08-18 — the count is 28.** Treemap was admitted under the escape clause above: recursive area subdivision is a layout grammar no existing type provides (bar encodes with length, nested with containment and no quantity, pyramid with rank). It shipped the full §10 set, and the counters named above moved 27 → 28 together with the prose.

The decision itself is unchanged — semantic patterns still never add a type, and the count still moves only for a new *layout* grammar. What this amendment records is the procedure: the two counters are this ADR's enforcement, so a PR that edits them without amending this file has quietly made itself the authority. Amend here in the same PR, or the number in the test is just whatever the last contributor typed.

**2026-08-18 — the count is 11 (automation-design fork).** ADR 0007 records the fork that repositioned this repository as Automation Design and cut the taxonomy 28 → 11 by deleting types outside the automation scope — a scope decision, not a violation of this record: patterns still never add a type. Ten automation semantic patterns were added (7 → 17 total), each routing to a kept type. The counters in `verify-semantic-motion.py` and `verify-docs-sync.py` moved with this amendment, per the procedure above.

**2026-08-18 — the pattern count is 18; the type count is still 11.** An eleventh automation pattern, **RPA solution blueprint**, was added after the fork above, and the pattern counter in `verify-semantic-motion.py` moved 17 → 18 with it. It routes to the existing **Flowchart** type (data flow when role lanes dominate, sequence for the runtime view), so it brings no new layout grammar and the visual-type count stays 11 — the rule this record exists to state, that patterns never add a type, is unchanged. ADR 0007's decision text now reads 11 automation patterns and 18 total.

The counter, however, moved first and the record followed. That is exactly what the procedure above forbids, so this amendment is the record it demands — written late, but written.

**2026-08-20 — the pattern count is 19; the type count is still 11.** **Agent card** was added, routing to the existing **Architecture** type: one agent documented as its architecture artifact (operating-mode chip, I/O spine, grounding container, tool boundary, guardrail gates, escalation). No new layout grammar — the counter in `verify-semantic-motion.py` moved 18 → 19 in the same commit as this amendment, per the procedure above.
