# Flowchart

**Best for:** decision logic, algorithms, user-facing branching flows ("Should I…?"), onboarding routing, support-triage trees.

## Layout conventions
- Shape carries type, not color:
  - **Oval** (`rx=20`) — start / end
  - **Rectangle** (`rx=6`) — step / action
  - **Diamond** — decision (≤3 exits)
  - **Small filled ink dot** (`r=4`) — merge point where branches rejoin
- Flow runs top→down. From a diamond, conventional exits: Yes to the right, No below — but label every outgoing arrow regardless.
- Use coral on the happy path *or* on the single most consequential decision — never on every decision.
- If two arrows must cross, use a small arc jump on one so the crossing is readable.

## Phased blueprint variant (RPA solution maps)

Used by the **RPA solution blueprint** semantic pattern: the end-to-end automation split into named processes, drawn as one continuous flow. This variant changes three conventions:

- **Flow runs left→right**, not top→down. Decision branches drop downward; rejoin via a right-then-up elbow into the bottom edge of the merge target.
- **Named phase bands**: each process gets an eyebrow label (`PROCESS 1 · MAIL INTAKE`, Geist Mono, uppercase, anchored at the band's left edge) and phases are separated by **dashed vertical dividers** (`ink @ 0.20`, dasharray `4,4`) spanning the content height. Dividers are decorative — connectors may cross them; that crossing *is* the handoff.
- **Activity-tag chips**: every activity rectangle carries a chip naming the *executing system class* — `MAIL`, `DOC AI`, `AGENT`, `HUMAN`, `RPA`, `API`, `APP`, `QUEUE` — drawn from the closed set in [`automation-primitives.md` § Activity tags](automation-primitives.md). Tags are **bare here, not glyph-prefixed** (that convention belongs to topology diagrams; see the same file's badge section). Vendor product names go in the sublabel, never in the tag.

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

### Detail set (overview + numbered process pages)

The deliverable for a detailed end-to-end process that exceeds any single-diagram budget — a 40-step automation is a *set of pages*, never one canvas. The set is:

1. **One overview** — the phased blueprint variant, each phase carrying its process number in the eyebrow (`PROCESS 1.2 · EMAIL AGENT`). Default size `print-a3-landscape` when the process has 4–5 phases; `print-a4-landscape` or `doc-wide` for 3 or fewer. Above 5 phases the overview compresses to phases-as-nodes (ladder rung 3 above) instead of full blueprint grammar — never a wider canvas.
2. **One process-detail page per phase** — the process-detail flavor above, its title number matching the overview eyebrow (`1.2 · Email agent answers`), step-ID chips continuing that numbering (`1.2.1`, `1.2.2`, …). Same size preset across all detail pages.

Rules that make it one deliverable instead of N loose files:

- **Numbering is the navigation.** Overview phase eyebrow ↔ detail-page title ↔ step-ID chips share one scheme, aligned to the PDD's section numbering when one exists. Never renumber between pages.
- **File naming:** `<base>-overview.html`, then `<base>-p<N>-<slug>.html` (e.g. `invoice-intake-p2-email-agent.html`) — the same overview-plus-parts shape as the faithful-import split in [output-spec.md §3](output-spec.md), with the process number in place of the zone name so filenames sort in PDD order.
- **Each page's footer colophon names the set**: `part 2 of 4 · invoice-intake` in the existing Geist Mono colophon slot, so a printed page still says where it belongs.
- **Handoffs stay visible.** A queue bridge or handoff at a phase boundary appears on *both* sides: as the outbound edge on the overview, and as the Start context on the consuming detail page (a muted, tagless entry node naming the source, e.g. `from 1.1 · intake queue`). Entry/exit context nodes don't count against the detail page's activity budget.
- **One fidelity ledger for the set**, reported once, listing what each page carries and what was cut — not one ledger per file.
- **Consistency is part of the taste gate:** same skin, same size preset on detail pages, same chip geometry, same legend across the set.

The set replaces — never accompanies — a single over-budget canvas. If a user insists on "everything on one page", the A3 blueprint at the extended budget above is the ceiling; past it, deliver the set and say why.

## Anti-patterns
- Using fill color to signal node type (shape does that).
- Decision diamond with 4+ exits — refactor into nested diamonds.
- Unlabeled decision branches.
- **Vendor product names as system tags** — the tag is the class (`HUMAN`), the sublabel is the product.
- **Queue drawn as a cylinder** — this design system has no cylinders; the Store/State treatment carries that meaning.
- **A phase without an eyebrow label** — an unlabeled dashed divider reads as decoration.

## Examples
- `assets/example-flowchart.html` — minimal light
- `assets/example-flowchart-dark.html` — minimal dark
- `assets/example-flowchart-full.html` — full editorial
- `assets/example-rpa-blueprint.html` — phased blueprint variant (3-process document-intake automation)
- `assets/example-process-detail.html` — process-detail flavor (numbered steps, under-box annotations, agent step with confidence gate)
