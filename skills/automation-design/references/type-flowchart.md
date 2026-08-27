# Flowchart

**Best for:** decision logic, algorithms, user-facing branching flows ("Should I…?"), onboarding routing, support-triage trees.

For a current-state, future-state, or migration-state process, also load [`process-profiles.md`](process-profiles.md). The profile adds evidence and state rules; this file continues to own decision shapes and control-flow geometry.

## Layout conventions
- Shape carries type, not color:
  - **Oval** (`rx=20`) — start / end
  - **Rectangle** (`rx=6`) — step / action
  - **Diamond** — decision (≤3 exits)
  - **Small filled ink dot** (`r=4`) — merge point where branches rejoin
- Flow runs top→down. From a diamond, conventional exits: Yes to the right, No below — but label every outgoing arrow regardless.
- Use mint on the happy path *or* on the single most consequential decision — never on every decision.
- If two arrows must cross, use a small arc jump on one so the crossing is readable.

## Phased blueprint variant (RPA solution maps)

Used by the **RPA solution blueprint** semantic pattern: the end-to-end automation split into named processes, drawn as one continuous flow. This variant changes three conventions:

- **Flow runs left→right**, not top→down. Decision branches drop downward; rejoin via a right-then-up elbow into the bottom edge of the merge target. **A dropped branch activity keeps the left→right grammar:** the decision's branch exit elbows down and then right, entering the activity's **left edge**, and the activity's outbound continues from its **right edge** — the **top edge is reserved for loop-back re-entry** (top = repetition, left = flow). When both exits of a decision drop to **sibling outcome branches**, place the siblings **symmetric about the diamond's vertical axis** — equal center offsets and equal widths, so neither outcome reads as an afterthought.
- **Named phase bands**: each process gets an eyebrow label (`PROCESS 1 · MAIL INTAKE`, Geist Mono, uppercase, anchored at the band's left edge) and phases are separated by **dashed vertical dividers** (`ink @ 0.20`, dasharray `4,4`) spanning the content height. Dividers are decorative — connectors may cross them; that crossing *is* the handoff.
- **Activity-tag chips**: every activity rectangle carries a chip naming the *system class that executes, hosts, or receives the step* — `MAIL`, `DOC AI`, `MODEL`, `AGENT`, `HUMAN`, `RPA`, `FLOW`, `API`, `APP`, `QUEUE` — drawn from the closed set in [`automation-primitives.md` § Activity tags](automation-primitives.md). Tags are **bare here, not glyph-prefixed** (that convention belongs to topology diagrams; see the same file's badge section). Vendor product names go in the sublabel, never in the tag.

  Chip geometry for both blueprint flavors: `28×10, rx=3`, Geist Mono 6px, hairline outline at `stroke @ 0.30`. That is shorter and lighter than the single `28×12 rx=2` 7px chip in SKILL.md §6 — a type-specific override, because these boxes are 104px wide and the process-detail flavor puts two chips on one edge. Use the same geometry for every chip in the diagram so they read as one system.

Additional primitives:

- **Queue bridge** — the decoupling point between a producing and a consuming process. Drawn as a Store/State rectangle (`ink @ 0.05` fill, `muted` stroke) with a `QUEUE` tag and an item count in the sublabel. Place it at the producing phase's outbound edge.
- **Human-validation branch** — a decision whose No/low-confidence exit drops to a `HUMAN` activity, then merges back. This branch is the usual focal candidate (accent on the human activity, not on every decision).

Budget: ≤3 phases, ≤5 activities per phase, ≤3 decisions total, exactly one queue bridge, one Start, ≤2 Ends. Phase banding is the sanctioned zoning that lets the total exceed the 9-node overview target — it is this exemption, not the faithful-import 24-node ceiling in [output-spec.md §3](output-spec.md), that governs a blueprint's node count.

One escalation ladder when the process outgrows the budget:

1. **≤3 phases** — any size preset, base budget above.
2. **4–5 phases** — `print-a3-landscape` only ([output-spec.md §2](output-spec.md)); the budget extends to **≤5 phases, ≤5 activities per phase, ≤5 decisions total, ≤2 queue bridges**. The larger canvas buys phases at the same print type ramp, never smaller type. Connector rules (SKILL.md §6) never relax — if 5 phases won't route cleanly on A3, move to rung 3.
3. **Above 5 phases** (or whenever rung 2 won't route) — the **detail set** (below) is mandatory, and its overview compresses: each phase collapses to one process node with its handoffs — the same zones-as-nodes move as the faithful-import split in output-spec.md §3 — so the overview stays inside the base budget at any phase count.

### Process-detail flavor (one numbered process, PDD-ready)

The level at which a solution-design document is written: one process per diagram, steps numbered against the document's section numbering. Same left→right grammar, phases omitted, three additions:

- **Numbered title and step-ID chips.** The page title carries the process number (`1.2 · Email agent answers`); every activity carries a **step-ID chip** in its top-left corner (`1.2.4`) and its activity tag moves to the top-right. IDs make the diagram navigable from the document text.

  The step-ID chip uses the same geometry as the activity tag (above), so the pair reads as one unit: ID left, tag right, both `28×10 rx=3` at 6px.
- **Under-box annotations.** Technical detail sits *below* the activity, not inside it: schedules (`daily · 08:00`), endpoints (`GET /suppliers`), entity names, thresholds. One line, Geist Mono 6.5px, `soft`, centered under the box with ≥10px clearance from any connector. The box keeps the business step; the annotation keeps the implementation fact.
- **Agent steps are first-class.** An `AGENT`-tagged activity followed by a **confidence gate** (`Confidence ≥ 80%?`) whose low exit drops to a `HUMAN` review task is the canonical hybrid shape. The agent step is the usual focal candidate.

Budget: 1 process, ≤8 activities, ≤3 decisions, ≤6 annotations, one Start, ≤2 Ends. More than 8 steps means the PDD section needs splitting too.

### Detail set (canonical hierarchy of numbered pages)

The deliverable for a detailed end-to-end process that exceeds any single-diagram budget — a 40-step automation is a *set of pages*, never one canvas. The set is a **canonical hierarchy with caller links** — a DAG, not a tree, because one page may be invoked from several call sites:

- **Canonical parent** — the page whose call site assigned this page its number. Exactly one per page, always; the page's number, file name, and `↑ parent` link derive from it.
- **Callers** — every page that links here, including the canonical parent. A reusable sub-routine (an `Excel_ReadSheet` invoked from two steps) has several; it is still drawn **once**, under its one canonical number, and every other call site links to that same file. Never duplicate a page under a second number.

The set contains:

1. **One overview** — the phased blueprint variant, each phase carrying its process number in the eyebrow (`PROCESS 2 · CATCH WEBHOOK`). Default size `print-a3-landscape` when the process has 4–5 phases; `print-a4-landscape` or `doc-wide` for 3 or fewer. Above 5 phases the overview compresses to phases-as-nodes (ladder rung 3 above) — never a wider canvas.
2. **One numbered page per sub-process, at any depth** — the process-detail flavor above, its title number matching the caller's reference (`2.0 · Catch webhook data`), step-ID chips continuing that numbering (`2.1`, `2.2`, …). A step that is itself a sub-process gets its own page one level deeper (`2.2.1`), recursively. Same size preset across all detail pages.

**Navigation is real hyperlinks, in two distinct mechanisms:**

- **Forward** (into a sub-process): the activity box whose action *is* "run sub-process N" is wrapped in an SVG `<a href="<file>">` around its shapes — diagram content, so it survives SVG/PNG export as part of the figure. Wrap the box, never a separate "go to" affordance.
- **Backward** (up and across): plain HTML links in the footer colophon — `↑ 2.0 · catch webhook data` to the canonical parent, and, on a page with several callers, a `CALLED FROM · 2.2 · 2.3` list linking each call site. This is meta-navigation about the deliverable, so it lives beside the existing `part N of M` colophon rather than inside the SVG. Word it as "called from", never "returns to" — a static link cannot know which caller the reader arrived from. End ovals are never wrapped in either direction; a page that terminates the whole process keeps a plain End.

Rules that make it one deliverable instead of N loose files:

- **Numbering is canonical across the set** and extends to arbitrary depth, aligned to the PDD's section numbering when one exists. Pages must never disagree about a number. Renumbering is forbidden except as an explicit structural revision (§ Revising a set), never as a side effect of a content edit.
- **File naming:** `<base>-overview.html`, then `<base>-p<number>-<slug>.html` with the dotted canonical number (`invoice-intake-p2-catch-webhook.html`, `invoice-intake-p2.2.1-excel-readsheet.html`) so filenames sort in PDD order — the same overview-plus-parts shape as the faithful-import split in [output-spec.md §3](output-spec.md).
- **Each page's footer colophon names the set**: `part 2 of 4 · invoice-intake` in the existing Geist Mono colophon slot, plus the `↑ parent` link and any `CALLED FROM` list (above).
- **Handoffs stay visible.** A queue bridge or handoff at a boundary appears on *both* sides: as the outbound edge on the caller, and as the Start context on the consuming page (a muted, tagless entry node naming the source, e.g. `from 1.1 · intake queue`). Entry/exit context nodes don't count against the page's activity budget.
- **One fidelity ledger for the set**, reported once, listing what each page carries and what was cut — not one ledger per file.
- **Consistency is part of the taste gate:** same skin, same size preset on detail pages, same chip geometry, same legend across the set.
- **Verify the set, not just the pages:** `python3 <skill-dir>/scripts/self_check.py --set <base>-overview.html` crawls the links and checks every target exists, every fragment resolves, and no two files claim one canonical number.
- **Annex pages may use any existing visual type.** A set may include non-flowchart annex pages — the **agent card** and **application card / screen contract** (Architecture; [semantic-patterns.md](semantic-patterns.md) §19–20), **screen states** (State machine), **runtime deployment topology** (Architecture) — carrying the same canonical numbering, colophon, `↑ parent` / `CALLED FROM` links, and `self_check.py --set` verification as every other page — the verifier checks link existence, fragments, and filename-number uniqueness only; concordance of in-page title, number, colophon, and `CALLED FROM` stays in the taste gate and the set-consistency rule. The invoking `AGENT`-tagged activity box is the forward SVG link to the card, exactly like a sub-process link, and the page-context panel defined here is reusable on annex pages.

The set replaces — never accompanies — a single over-budget canvas. If a user insists on "everything on one page", the A3 blueprint at the extended budget above is the ceiling; past it, deliver the set and say why.

### Loop-back, exception terminals, and the page-context panel

Three primitives that PDD-depth pages need; all live inside the existing Flowchart grammar.

**Loop-back (pagination / retry).** A decision whose "more remain" exit re-enters an earlier step — batch inserts, offset pagination, bounded retries. Route the exit **above** the main left→right row via rounded elbows, re-entering the **top edge** of the repeated node; the arc must clear every box and label it passes by the §6 connector margins — reroute rather than graze. The edge label obeys the standard budget (≤14 chars, all-caps): `YES · +BATCH`, `MORE · +OFFSET`. The exact expression (`Skip += BatchSize`) goes in the repeated node's **under-box annotation**, never in the edge label. A loop-back counts against the page's decision budget; it does not get its own budget line.

**Exception terminal (BE / SE).** A branch end that is not the process's true End: a rectangle (not an oval) named by a short mono code (`BE001`, `SE003`) with a one-line message below. Both use the `danger` role from [`style-guide.md`](style-guide.md) — `danger-tint` fill, `danger` stroke — with stroke style separating the two classes: **BE** (business exception) solid, **SE** (system exception) dashed `4,3`. `danger` is reserved for exactly this (it is not a second accent; the focal element stays mint). Distinct from `EXC` in [`automation-primitives.md`](automation-primitives.md): `EXC` types an exception as an *actor/outcome* in topology diagrams and an edge kind; the BE/SE terminal is a flowchart branch terminus identified by a PDD code. BE/SE codes never appear in an activity-tag chip. Budget: **≤4 exception terminals per page**, on top of the ≤2 End ovals — more means the branches need consolidating or the page needs splitting.

**Page-context panel.** A page-level fact box — trigger mechanism, schedule, inputs consumed — that describes the page as a whole rather than pointing at one node (that job belongs to the [annotation callout](primitive-annotation.md)). It lives **inside the SVG**, in a reserved top band of the `viewBox`, exactly as the legend strip reserves the bottom band — an HTML `<div>` above the SVG would silently vanish from every `.svg`/`.png` export. Draw it as a `paper-2`-filled, hairline-bordered rect with a Geist Mono uppercase eyebrow (`TRIGGER MECHANISM`, `INPUTS`) and up to ~5 short mono lines. Budget: at most one per page; more content than that belongs in the surrounding document, not the panel.

### Revising a set

How to apply feedback to a delivered set without regenerating it wholesale:

1. **Locate, don't guess.** Map the feedback to the numbering (a phase/step reference or a quoted label) to find the exact file and node. If it doesn't resolve to one page unambiguously, ask.
2. **Edit only the touched page(s).** The HTML is the source of truth; never hand-edit an exported `.drawio` or read one back — translate the words into an HTML edit.
3. **Propagate only what must propagate.** A content edit (label fix, added step within budget) stays on its page and never touches numbering. A **structural** change (add/remove/reorder a phase or numbered process) is the only case where renumbering is allowed — and it is one atomic pass updating: overview eyebrows, the affected page's title and step-ID chips, every `↑ parent` / `CALLED FROM` link and file name pointing at the renumbered page, and the `part N of M` colophon on every page. Never leave two pages disagreeing about a number.
4. **Re-verify at set scope.** Taste gate (SKILL.md §9) on the touched pages, then `self_check.py --set` across the whole set — a local edit is the easiest way to silently break a cross-page link.
5. **Re-export what was regenerated.** If `.drawio`/`.png`/`.svg` existed for a touched page, regenerate them from the updated HTML ([export.md](export.md) / [export-drawio.md](export-drawio.md)). Never leave a stale export beside an updated HTML.
6. **Report what changed** — which files, what rippled, what was re-exported. Short and specific, in the spirit of the fidelity ledger.

## Anti-patterns
- Using fill color to signal node type (shape does that).
- Decision diamond with 4+ exits — refactor into nested diamonds.
- Unlabeled decision branches.
- **Vendor product names as system tags** — the tag is the class (`HUMAN`), the sublabel is the product.
- **Queue drawn as a cylinder** — this design system has no cylinders; the Store/State treatment carries that meaning.
- **A phase without an eyebrow label** — an unlabeled dashed divider reads as decoration.
- **"Returns to" wording on a caller link** — a static link cannot know the reader's path; the footer says `↑ parent` and `CALLED FROM`, never "returns to where you came from".
- **A reused sub-routine duplicated under a second number** — one page, one canonical number, many callers.
- **Loop-back edge label carrying the loop expression** — `YES · Skip += BatchSize` breaks the ≤14-char all-caps label budget; the expression is an under-box annotation.
- **BE/SE code in an activity-tag chip** — exception codes name terminals, not executing systems.
- **Page-context panel as an HTML `<div>`** — it must live inside the SVG viewBox or it vanishes from every export.
- **A dropped branch activity entered from the top** — top entry means loop-back; branch flow enters the left edge and exits the right.
- **Sibling outcome branches at unequal offsets or widths** under one decision — symmetry about the diamond's axis is the convention.

## Examples
- `assets/example-flowchart.html` — minimal light
- `assets/example-flowchart-dark.html` — minimal dark
- `assets/example-flowchart-full.html` — full editorial
- `assets/example-rpa-blueprint.html` — phased blueprint variant (3-process document-intake automation)
- `assets/example-process-detail.html` — process-detail flavor (numbered steps, under-box annotations, agent step with confidence gate)
- `assets/example-detail-set-overview.html` — detail-set overview (phases-as-nodes, forward SVG link into 2.0)
- `assets/example-detail-set-p2-catch-webhook.html` — numbered page: loop-back, BE/SE exception terminals, page-context panel, forward links to a reused sub-routine
- `assets/example-detail-set-p2.2.1-excel-readsheet.html` — reused sub-routine page (`↑ parent` + `CALLED FROM · 2.2 · 2.3` colophon)
