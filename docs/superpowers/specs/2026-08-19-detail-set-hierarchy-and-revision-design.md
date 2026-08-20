# Detail-set hierarchy, RPA loop/exception primitives, and revision workflow

**Status:** proposed
**Date:** 2026-08-19
**Scope:** `skills/automation-design/references/type-flowchart.md` (Detail set section), with small cross-references from `automation-primitives.md` and `primitive-annotation.md`, a documentation-only addition to `export-drawio.md`, and a required scope addition to `scripts/self_check.py`. No changes to `output-spec.md`'s dials, `style-guide.md`'s semantic roles, `mxgraph_emit.py`'s behavior, or the 11-type / 18-pattern taxonomy.

## 1. Context

Real-world RPA solution-design documents (PDDs) — the reference material for this change is a set of drawio-exported Receiver/Performer/Dispatcher/Reporter timesheet and invoice-extraction process maps — are routinely deeper and more cross-linked than this skill's current **Detail set** ([type-flowchart.md § Detail set](../../../skills/automation-design/references/type-flowchart.md)) assumes:

- The set is a **DAG of pages, not two levels** — not strictly a tree, because a page can be reused from more than one call site. A high-level map links into numbered sub-process pages (`1.0`, `2.0`, `3.0`), and those link into further named sub-routine pages (`3.2.1 Excel_ReadSheet`), sometimes **reused from more than one call site**.
- Pages carry **real navigation** — every source page ends with "Start (S)/End (E) Nodes will return you to the upper-level maps," i.e. the Start/End nodes are literal links, not a naming convention a reader infers. A reused page has more than one inbound link, so "return to the upper-level map" can't mean a single fixed link the way it does for a page with one caller.
- Individual pages contain patterns the current type-flowchart grammar has no primitive for: **pagination/retry loops** (a decision whose "yes, more remain" exit re-enters an earlier node with an incremented offset), **exception-coded terminal nodes** (`BE001`, `SE003` — a branch end that is not the process's true End), and a **page-level context panel** (Trigger Mechanism / Inputs) that describes the page as a whole rather than pointing at one node.
- These documents get **revised** after first delivery — a stakeholder reads page `3.2` and asks for a step to be added, a loop label corrected, a phase renumbered. The skill needs a defined, minimal-diff way to apply that without regenerating (and silently drifting) the rest of the set.

This is an **architectural** change per the brainstorming skill's classification: it restructures the Detail set contract that other reference files (and any previously generated output) depend on, and adds new primitives, not a one-file fix.

## 2. Decision

**Approach A** (of three considered — see chat transcript for B/minimal and C/new-pattern alternatives): extend the existing Detail set section in place. No new visual type, no new semantic pattern, no new color role. Everything below routes to the existing **Flowchart** type via the existing **RPA solution blueprint** pattern, per ADR 0002/0007 — the taxonomy counters (11 types, 18 patterns) do not move.

Six pieces, all scoped to `type-flowchart.md § Detail set` unless noted:

### 2.1 Canonical hierarchy + caller links (not a tree)

Replace the fixed "one overview + one page per phase" shape with a hierarchy that is precisely a **DAG, not a tree**, once reuse is allowed. Two roles, named explicitly so the model stays unambiguous when a page has more than one inbound reference:

- **Canonical parent** — the page whose call site *assigned* the page its number. Exactly one per page, always. This is what the page's number, file name, and "↑ parent" link are derived from.
- **Callers** — every page that links to this page, including the canonical parent. A page invoked from a single site has one caller (= its canonical parent). A reusable sub-routine (e.g. `Excel_ReadSheet` called from two places inside `3.2`) has several.

Rules:

- Numbering is canonical across the set and extends to arbitrary depth (`1.2.1`, `1.2.1.3`, …). Pages must never disagree about a number. Casual renumbering is forbidden; renumbering is only valid as an explicit structural revision (§2.6 rule 3), never as a side effect of an unrelated edit.
- A reusable page is drawn **once**, under the number its canonical parent assigned, and every other caller links to that same file — it is never duplicated under a second number.
- File naming extends the existing `<base>-p<N>-<slug>.html` scheme with dotted segments matching the canonical number: `<base>-p3.2.1-excel-readsheet.html`.
- The overview-compresses-at-depth rule (existing: >5 phases collapses the overview to phases-as-nodes) still applies at the top level only; deeper levels are reached by drilling in, not by flattening the overview further.

### 2.2 Real hyperlink navigation

Forward links (an activity box whose action *is* "run sub-process N") are real `<a href="...">` wraps around the SVG shape — diagram content, so it must survive as a clickable element of the diagram itself. Backward links (`↑ parent`, `CALLED FROM`) live in the footer colophon as plain HTML links, the same slot the existing "part N of M" text already occupies — meta-navigation about the deliverable, not diagram content, so it doesn't need to survive SVG/PNG export the way the forward link and the page-context panel (§2.5) do. The End oval itself is never wrapped, in either direction. Navigation is **static hyperlinking, not call-stack return** — a page cannot know, from a link alone, which caller the reader arrived from, so forward and backward links use these two different mechanisms rather than one shared "linked oval" idiom:

- Every page gets exactly **one `↑ parent` link**, in the footer colophon, to its **canonical parent** — well-defined regardless of how many callers the page has: `↑ 3.2 · build escalation report`.
- A page with **more than one caller** additionally lists them in the footer, each a separate link, under a `CALLED FROM` label: `CALLED FROM · 3.2.4 · 4.1.2`. This is presented as "other places that link here," not as "return to where you came from" — the wording must not imply the link knows the reader's path.
- An activity box on a caller page whose action *is* "run sub-process N" is itself the link forward — wrap the box, not a separate "go to" affordance.
- A page that terminates the whole process (a true process End, not a sub-routine return point) keeps a plain, non-linked End oval.
- This is additive to the existing "part N of M" colophon, not a replacement.

### 2.3 Loop-back (pagination/retry) primitive

New primitive for "more batches/pages remain" loops, distinct from a flowchart merge point:

- Drawn as the decision diamond's "more remain" exit routed **above** the main left-right row via a rounded elbow, re-entering the **top edge** of the earlier node it repeats. The arc must clear every node and label it passes over by the standard connector-rule margins (SKILL.md §6) — reroute rather than let it graze a box.
- The edge label follows the existing arrow-label budget (SKILL.md §6 / `automation-primitives.md` § Edge kinds: **≤14 characters, all-caps**) — no exception for this primitive. `YES · Skip += BatchSize` is 24 characters and mixed case, so it does not qualify as the edge label. Use a short label that fits (`MORE · +BATCH`, `YES · +OFFSET`) and, if the exact variable/expression matters, carry it as an **under-box annotation** on the repeated node — the process-detail flavor's existing primitive for implementation detail (schedules, endpoints, thresholds) — rather than inventing a longer-label exception.
- Counts against the page's existing decision budget (process-detail flavor: ≤3 decisions); it does not get its own separate budget line.

### 2.4 Exception-terminal (BE/SE) primitive

A branch-ending node that is not the process's true End:

- Drawn as a rectangle (not an oval), carrying a short mono code (`BE001`, `SE003`) as the node name and a one-line message below it.
- ~~No new color role. Business exceptions (BE) use a solid `ink` stroke; system exceptions (SE) use the existing dashed `ink @ 0.20` stroke.~~ **Amended 2026-08-20 (user decision during implementation):** a `danger` semantic role (`#a63d40` brick light / `#c96b6d` dark, plus `danger-tint`) was added to `style-guide.md`. Both terminal classes use `danger-tint` fill and a `danger` stroke; stroke style still separates them — BE solid, SE dashed `4,3`. `danger` is explicitly not a second accent: reserved for exception terminals and failure marking, budgeted by the ≤4-terminals cap, never for emphasis.
- **Distinct from the `EXC` primitive in `automation-primitives.md`.** `EXC` is a topology-diagram node primitive (an exception treated as an *actor/outcome* in architecture/data-flow diagrams) and an edge kind (`SYS EXC`, `ESCALATE` on a connector). The BE/SE exception-terminal is a **Flowchart / process-detail primitive**: a branch terminus inside a numbered process page, identified by a PDD-style code. BE/SE codes are not activity tags and never appear in the activity-tag chip; the two vocabularies don't mix on the same node.
- Counts as a terminal, not as an End oval — a page may have several exception terminals in addition to its ≤2 End ovals, capped at **≤4 exception terminals per page**. More than that signals the branches need consolidating (a shared validation step feeding one terminal) or the page needs splitting; it is not a case for raising the cap.

### 2.5 Page-context panel primitive

A page-level fact box, distinct from the existing italic-serif annotation callout (which always points at one node):

- **Lives inside the SVG, in a reserved top band of the `viewBox` — never an HTML `<div>` above the `<svg>`.** `export.md` exports the `<svg>` node only and explicitly never uses `foreignObject` to fold an HTML wrapper in; a context panel drawn as page HTML would render fine in the browser and then silently vanish from every `.png`/`.svg` export. Model it the same way the existing bottom legend strip is modeled (SKILL.md §6: expand the `viewBox` and draw the strip as SVG rects/text) — here, expand the `viewBox` height by a top band instead of (or in addition to) the bottom one.
- `paper-2` fill, hairline border, Geist Mono uppercase eyebrow (`TRIGGER MECHANISM`, `INPUTS`) followed by a short bullet list in body type, all as SVG shapes/text.
- Describes the page as a whole (schedule, trigger, inputs/assets consumed) — content that would otherwise force an artificial "annotation pointing at the Start node."
- Budget: at most one context panel per page; if a page needs more than ~5 bullet lines, that's a sign the content belongs in the surrounding prose/deliverable text, not the panel.

### 2.6 Revising a set (feedback workflow)

New subsection documenting how to apply user feedback to an already-delivered set without regenerating it wholesale:

1. **Locate**, don't guess. Map the feedback to the numbering scheme (phase/step reference, or a quoted label) to find the exact file and node. If the feedback doesn't resolve to a single page unambiguously, ask which one rather than editing the nearest match.
2. **Edit only the touched page(s).** The HTML is the source of truth (existing rule from `export.md`/`export-drawio.md`); never hand-edit an exported `.drawio` or ask the user for one back — translate their words into an HTML edit.
3. **Propagate only what must propagate.** A content-only change (fixing a label, adding a step within a page) stays on that page and never touches numbering. A **structural** change (adding/removing/reordering a phase or a numbered process) is the one case where renumbering is allowed at all (§2.1) — and when it happens, it is a single atomic edit that updates, in the same pass: the overview's phase eyebrows, the affected page's title and step-ID chips, every `↑ parent` / `CALLED FROM` link and canonical file name pointing at the renumbered page, and the `part N of M` colophon on every page in the set. Never leave two pages disagreeing about a number, and never renumber as a side effect of an unrelated content edit.
4. **Re-verify at set scope, not just page scope.** Run the SKILL.md §9 taste gate on the touched page(s), but re-check numbering/hyperlink consistency across the *whole* set before delivering — a local edit is the easiest way to silently break a cross-page reference.
5. **Re-export what was regenerated.** If `.drawio`/`.png`/`.svg` had previously been produced for a touched page, regenerate them from the updated HTML via `export.md`/`export-drawio.md`. Don't leave a stale export beside an updated HTML.
6. **Report what changed**, in the same spirit as the fidelity ledger: which file(s) changed, what rippled, what was regenerated. Short and specific, not a full re-statement of the set.

## 3. Non-goals (explicitly out of scope for this change)

- **No drawio round-trip/merge.** Feedback arrives in words and is applied to the HTML; a user's manual edits inside an exported `.drawio` are never read back or reconciled. (Decided explicitly in chat — this was considered and rejected as a much larger, philosophy-contradicting feature.)
- **No new visual type or semantic pattern.** Everything above is a Detail-set / Flowchart-type extension.
- ~~**No new style-guide color role.**~~ Superseded by the 2026-08-20 amendment in §2.4: the user opted into the `danger` role during implementation.
- **No change to `drawio_extract.py` or the import-drawio flow.** The primary path this change serves is from-scratch generation from a written process description; import-side multi-page/link-following support is a separate, later piece of work if ever needed.

## 4. Files touched

- `skills/automation-design/references/type-flowchart.md` — rewrite/extend the **Detail set** subsection (§2.1–2.2 above), and add the loop-back, exception-terminal, and page-context primitives either inline or as short new subsections near the existing process-detail flavor. Add the **Revising a set** subsection (§2.6).
- `skills/automation-design/references/automation-primitives.md` — no taxonomy change; confirm/cross-reference that vendor system names (Orchestrator, Excel, Outlook, SharePoint, Maconomy, Data Fabric, UiPath) already map to existing tags (`APP`, `API`, `RPA`) with the vendor name in the sublabel, per the existing "vendor names never become tags" rule. Add a one-line cross-reference from the new primitives to this mapping if not already obvious.
- `skills/automation-design/references/primitive-annotation.md` — one cross-reference line distinguishing the page-context panel (new) from the pointer callout (existing), so an author doesn't reach for the wrong one.
- New example asset(s) under `skills/automation-design/assets/` demonstrating: a 3-level linked mini-set (overview → phase page → reused sub-routine page) with working relative hyperlinks, one page showing the loop-back primitive, one page showing an exception terminal and a page-context panel. Exact file list decided during planning.
- `skills/automation-design/scripts/self_check.py` — **required, not optional**, since navigation is now part of the contract (§2.2) rather than a naming convention: a broken link is a broken deliverable. Add a set-scoped mode (`--set <overview.html>` or equivalent) that crawls local `<a href>` targets reachable from the overview and checks: (a) every referenced file exists on disk, (b) every `#fragment` target exists in its target file, (c) no two files claim the same canonical number. Scope is deliberately narrow — existence and consistency, not a general link crawler.
- `skills/automation-design/references/export-drawio.md` — add **hyperlinks / `<a href>` wraps** to the existing "What does not [survive translation]" table, alongside pattern fills and motion. This documents current behavior; it does not change `mxgraph_emit.py`.

## 5. Open questions / future work

- Whether `mxgraph_emit.py` should be extended to carry navigation links into the exported `.drawio` (draw.io cells support a `link` style) — deferred. Out of scope for this change per the non-goals (§3); the spec instead documents the current gap in `export-drawio.md` rather than silently leaving it undocumented.
- Whether the import-drawio path should eventually gain the same hierarchy/navigation support for multi-page source files — deferred; the user confirmed from-scratch generation is the primary path for now.
- ~~Whether a future project will want a dedicated "danger/risk" style-guide color role for exception terminals.~~ Resolved 2026-08-20: added (§2.4 amendment).

## 6. Verification impact

- `verify-docs-sync.py` / `verify-semantic-motion.py` counters (type count 11, pattern count 18) are unaffected — no new type, no new pattern.
- `verify-geometry.py` continues to apply unchanged to any new example assets (label/connector rules are not relaxed by this change).
- New example assets must pass the existing SKILL.md §9 taste gate and the self-check script before being committed.
