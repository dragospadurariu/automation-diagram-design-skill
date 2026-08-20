# Detail-Set Hierarchy, RPA Primitives & Revision Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the automation-design skill so a written PDD can become a linked, arbitrary-depth set of flowchart pages (canonical hierarchy + reuse), with loop-back, BE/SE exception-terminal, and page-context-panel primitives, a set-scoped link verifier, and a documented revision workflow.

**Architecture:** Documentation-first change to `type-flowchart.md` (the Detail set contract), plus one new verification mode in the packaged `self_check.py`, three one-line cross-references in sibling reference files, and a 3-page linked example set under `assets/` that exercises every new primitive and passes every existing CI gate.

**Tech Stack:** Markdown reference docs, hand-authored SVG-in-HTML diagram assets, Python 3.9+ stdlib-only scripts (repo convention), existing verifier suite (`self_check.py`, `verify-geometry.py`, `lint-skin.py`, `verify-docs-sync.py`).

**Spec:** `docs/superpowers/specs/2026-08-19-detail-set-hierarchy-and-revision-design.md`

## Global Constraints

- No new visual type, no new semantic pattern, no new style-guide color role (spec §3; ADR 0002/0007 counters stay at 11 types / 18 patterns).
- No change to `drawio_extract.py`, `import-drawio.md`, or `mxgraph_emit.py` behavior (spec §3).
- Arrow labels: ≤14 characters, all-caps (SKILL.md §6; `automation-primitives.md` § Edge kinds) — the loop-back label must comply.
- Exception terminals: ≤4 per page; BE = solid `ink` stroke, SE = dashed `ink @ 0.20` stroke (spec §2.4).
- Page-context panel lives **inside** the SVG viewBox (reserved top band), never an HTML `<div>` (spec §2.5).
- Forward navigation = SVG `<a>` wrap around the activity shape; backward navigation (`↑ parent`, `CALLED FROM`) = HTML links in the footer colophon; End ovals are never wrapped (spec §2.2).
- All SVG coordinates/sizes divisible by 4 (SKILL.md §7); every diagram passes the §9 taste gate, `self_check.py`, `verify-geometry.py`, and `lint-skin.py --all --baseline`.
- Python: stdlib only, `from __future__ import annotations` at top (repo convention in `self_check.py`).
- CI requires a synchronized plugin version bump when skill content changes (`verify-plugin-package.py`) — done once in the final task.
- Repo root for all paths below: `/mnt/d/projects/automation-design`.

---

### Task 1: Set-scoped link verification in `self_check.py`

**Files:**
- Modify: `skills/automation-design/scripts/self_check.py`
- Test: `scripts/test-self-check.py`

**Interfaces:**
- Produces: `verify_set(overview: Path) -> list[str]` in `self_check.py` (module-level function, importable by the test script the same way `verify` already is), and a `--set` CLI flag: `python3 self_check.py --set <overview.html> [...]`.
- Consumes: existing `verify(path) -> list[str]`, `parsed_document(source) -> DiagramParser`, and `DiagramParser.references: list[tuple[tag, rel, value]]` (already collects `href` on `<a>`, including SVG `<a>`).

- [ ] **Step 1: Write the failing tests**

Append to `scripts/test-self-check.py`, before the `if failures:` block in `main()` (reusing the already-loaded `module`). A minimal valid page must pass the existing per-file `verify()`, so the helper builds one that satisfies the accessible-SVG contract:

```python
    # ---- set-scoped link verification (--set mode) ----

    def minimal_page(slug: str, body_svg: str, footer: str = "") -> str:
        return (
            "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"UTF-8\">\n"
            f"<title>{slug}</title>\n</head>\n<body>\n"
            f"<svg viewBox=\"0 0 96 48\" xmlns=\"http://www.w3.org/2000/svg\" role=\"img\" "
            f"aria-labelledby=\"{slug}-title {slug}-desc\">\n"
            f"<title id=\"{slug}-title\">{slug}</title>\n"
            f"<desc id=\"{slug}-desc\">Test fixture page.</desc>\n"
            f"{body_svg}\n</svg>\n{footer}\n</body>\n</html>\n"
        )

    def check_set(label: str, files: dict[str, str], overview: str, needle: str | None) -> None:
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            for name, source in files.items():
                (root / name).write_text(source, encoding="utf-8")
            errors = module.verify_set(root / overview)
        if needle is None:
            if errors:
                failures.append(f"{label}: expected clean set, got {errors}")
            else:
                print(f"OK: {label} passes")
        elif not any(needle in error for error in errors):
            failures.append(f"{label}: expected an error containing {needle!r}, got {errors}")
        else:
            print(f"OK: {label} rejected")

    check_set(
        "valid linked set",
        {
            "mini-overview.html": minimal_page(
                "ov",
                '<a href="mini-p2-catch.html"><rect width="96" height="48" id="ov-n1"/></a>',
            ),
            "mini-p2-catch.html": minimal_page(
                "p2",
                '<a href="mini-p2.2.1-readsheet.html#p21-start"><rect width="96" height="48"/></a>',
                '<footer><a href="mini-overview.html">parent</a></footer>',
            ),
            "mini-p2.2.1-readsheet.html": minimal_page(
                "p21",
                '<rect id="p21-start" width="96" height="48"/>',
                '<footer><a href="mini-p2-catch.html">parent</a></footer>',
            ),
        },
        "mini-overview.html",
        None,
    )
    check_set(
        "missing link target",
        {
            "mini-overview.html": minimal_page(
                "ov", '<a href="mini-p9-ghost.html"><rect width="96" height="48"/></a>'
            ),
        },
        "mini-overview.html",
        "does not exist",
    )
    check_set(
        "missing fragment",
        {
            "mini-overview.html": minimal_page(
                "ov", '<a href="mini-p2-catch.html#no-such-id"><rect width="96" height="48"/></a>'
            ),
            "mini-p2-catch.html": minimal_page("p2", '<rect width="96" height="48"/>'),
        },
        "mini-overview.html",
        "fragment",
    )
    check_set(
        "duplicate canonical number",
        {
            "mini-overview.html": minimal_page(
                "ov",
                '<a href="mini-p2-catch.html"><rect width="96" height="48"/></a>'
                '<a href="mini-p2-other.html"><rect y="0" width="96" height="48"/></a>',
            ),
            "mini-p2-catch.html": minimal_page("p2", '<rect width="96" height="48"/>'),
            "mini-p2-other.html": minimal_page("p2b", '<rect width="96" height="48"/>'),
        },
        "mini-overview.html",
        "canonical number",
    )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 scripts/test-self-check.py`
Expected: `AttributeError: module 'self_check' has no attribute 'verify_set'` (or equivalent failure) — the new checks fail, the pre-existing checks still pass up to that point.

- [ ] **Step 3: Implement `verify_set` and the `--set` flag**

In `skills/automation-design/scripts/self_check.py`, add after the existing `verify()` function (imports `unquote` is already available via `urllib.parse` — extend the existing import line `from urllib.parse import urlparse` to `from urllib.parse import unquote, urlparse`):

```python
CANONICAL_NUMBER_RE = re.compile(r"-p(\d+(?:\.\d+)*)-")
ID_ATTR_RE = re.compile(r"""\bid\s*=\s*["']([^"']+)["']""")


def _is_local_target(value: str) -> bool:
    stripped = value.strip()
    if not stripped or stripped.startswith("#"):
        return False
    lowered = stripped.casefold()
    if lowered.startswith(("http://", "https://", "//", "data:", "javascript:", "mailto:")):
        return False
    if ":" in stripped.split("/", 1)[0]:
        return False
    return True


def verify_set(overview: Path) -> list[str]:
    """Crawl local <a href> targets from *overview* and check set consistency.

    Three checks, deliberately narrow (spec: existence and consistency, not a
    general crawler): every linked local file exists, every #fragment resolves
    to an id in its target, and no two files claim the same canonical page
    number (the -pN.N- segment of the detail-set naming scheme). Each reached
    HTML file also gets the standard per-file verify().
    """
    errors: list[str] = []
    seen: set[Path] = set()
    numbers: dict[str, Path] = {}
    queue: list[Path] = [overview.resolve()]
    while queue:
        path = queue.pop(0)
        if path in seen:
            continue
        seen.add(path)
        if not path.is_file():
            errors.append(f"{path.name}: linked file does not exist")
            continue
        match = CANONICAL_NUMBER_RE.search(path.name)
        if match:
            number = match.group(1)
            claimant = numbers.setdefault(number, path)
            if claimant != path:
                errors.append(
                    f"canonical number {number} claimed by both "
                    f"{claimant.name} and {path.name}"
                )
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"{path.name}: {exc}")
            continue
        errors.extend(f"{path.name}: {error}" for error in verify(path))
        parser = parsed_document(source)
        ids = set(ID_ATTR_RE.findall(source))
        for tag, _rel, value in parser.references:
            if tag != "a":
                continue
            stripped = value.strip()
            if stripped.startswith("#"):
                if stripped[1:] not in ids:
                    errors.append(
                        f"{path.name}: fragment {stripped} has no matching id"
                    )
                continue
            if not _is_local_target(stripped):
                continue
            target, _, fragment = stripped.partition("#")
            resolved = (path.parent / unquote(target)).resolve()
            if not resolved.is_file():
                errors.append(
                    f"{path.name}: link target {target!r} does not exist"
                )
                continue
            if fragment:
                target_source = resolved.read_text(encoding="utf-8")
                if fragment not in set(ID_ATTR_RE.findall(target_source)):
                    errors.append(
                        f"{path.name}: fragment #{fragment} not found in {resolved.name}"
                    )
            if resolved.suffix.casefold() in {".html", ".htm"}:
                queue.append(resolved)
    return errors
```

And in `main()`, add the flag and branch (replace the body of the `for path in args.files:` loop's `try:` line context):

```python
    argument_parser.add_argument(
        "--set",
        action="store_true",
        help="treat each file as a detail-set overview and verify the whole linked set",
    )
```

with the per-file call becoming:

```python
        try:
            errors = verify_set(path) if args.set else verify(path)
        except (OSError, UnicodeError) as exc:
            errors = [str(exc)]
```

Also extend the module docstring's first paragraph with one sentence: `With --set, the file is treated as a detail-set overview and every locally linked page is crawled and checked (existence, fragments, canonical-number uniqueness).`

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 scripts/test-self-check.py`
Expected: all pre-existing checks still `OK`, plus `OK: valid linked set passes`, `OK: missing link target rejected`, `OK: missing fragment rejected`, `OK: duplicate canonical number rejected`, ending `All self-check tests passed`.

- [ ] **Step 5: Commit**

```bash
git add skills/automation-design/scripts/self_check.py scripts/test-self-check.py
git commit -m "feat: add --set mode to self_check for detail-set link verification"
```

---

### Task 2: Rewrite `type-flowchart.md` § Detail set + new primitives + revision workflow

**Files:**
- Modify: `skills/automation-design/references/type-flowchart.md` (replace the `### Detail set` section; extend the process-detail flavor's Additional-primitives area; extend Anti-patterns and Examples)

**Interfaces:**
- Produces: the section headings `### Detail set (canonical hierarchy of numbered pages)`, `### Loop-back, exception terminals, and the page-context panel`, `### Revising a set` — Task 4's assets must conform to these rules, and Task 3's cross-references cite them.
- Consumes: existing chip geometry (`28×10 rx=3`, 6px), under-box annotation, and colophon conventions already defined in the same file.

- [ ] **Step 1: Replace the `### Detail set (overview + numbered process pages)` section**

Replace the entire section (from its heading through the paragraph ending `…deliver the set and say why.`) with:

````markdown
### Detail set (canonical hierarchy of numbered pages)

The deliverable for a detailed end-to-end process that exceeds any single-diagram budget — a 40-step automation is a *set of pages*, never one canvas. The set is a **canonical hierarchy with caller links** — a DAG, not a tree, because one page may be invoked from several call sites:

- **Canonical parent** — the page whose call site assigned this page its number. Exactly one per page, always; the page's number, file name, and `↑ parent` link derive from it.
- **Callers** — every page that links here, including the canonical parent. A reusable sub-routine (an `Excel_ReadSheet` invoked from two steps) has several; it is still drawn **once**, under its one canonical number, and every other call site links to that same file. Never duplicate a page under a second number.

The set contains:

1. **One overview** — the phased blueprint variant, each phase carrying its process number in the eyebrow (`PROCESS 2 · CATCH WEBHOOK`). Default size `print-a3-landscape` when the process has 4–5 phases; `print-a4-landscape` or `doc-wide` for 3 or fewer. Above 5 phases the overview compresses to phases-as-nodes (ladder rung 3 above) — never a wider canvas.
2. **One numbered page per sub-process, at any depth** — the process-detail flavor, its title number matching the caller's reference (`2.0 · Catch webhook data`), step-ID chips continuing that numbering (`2.1`, `2.2`, …). A step that is itself a sub-process gets its own page one level deeper (`2.2.1`), recursively. Same size preset across all detail pages.

**Navigation is real hyperlinks, in two distinct mechanisms:**

- **Forward** (into a sub-process): the activity box whose action *is* "run sub-process N" is wrapped in an SVG `<a href="<file>">` around its shapes — diagram content, so it survives SVG/PNG export as part of the figure. Wrap the box, never a separate "go to" affordance.
- **Backward** (up and across): plain HTML links in the footer colophon — `↑ 2.0 · catch webhook data` to the canonical parent, and, on a page with several callers, a `CALLED FROM · 2.2 · 2.3` list linking each call site. This is meta-navigation about the deliverable, so it lives beside the existing `part N of M` colophon rather than inside the SVG. Word it as "called from", never "returns to" — a static link cannot know which caller the reader arrived from. End ovals are never wrapped in either direction; a page that terminates the whole process keeps a plain End.

Rules that make it one deliverable instead of N loose files:

- **Numbering is canonical across the set** and extends to arbitrary depth, aligned to the PDD's section numbering when one exists. Pages must never disagree about a number. Renumbering is forbidden except as an explicit structural revision (§ Revising a set), never as a side effect of a content edit.
- **File naming:** `<base>-overview.html`, then `<base>-p<number>-<slug>.html` with the dotted canonical number (`invoice-intake-p2-catch-webhook.html`, `invoice-intake-p2.2.1-excel-readsheet.html`) so filenames sort in PDD order.
- **Each page's footer colophon names the set**: `part 2 of 4 · invoice-intake`, plus the `↑ parent` link and any `CALLED FROM` list (above).
- **Handoffs stay visible.** A queue bridge or handoff at a boundary appears on *both* sides: as the outbound edge on the caller, and as the Start context on the consuming page (a muted, tagless entry node naming the source, e.g. `from 1.1 · intake queue`). Entry/exit context nodes don't count against the page's activity budget.
- **One fidelity ledger for the set**, reported once — not one per file.
- **Consistency is part of the taste gate:** same skin, same size preset on detail pages, same chip geometry, same legend across the set.
- **Verify the set, not just the pages:** `python3 <skill-dir>/scripts/self_check.py --set <base>-overview.html` crawls the links and checks every target exists, every fragment resolves, and no two files claim one canonical number.

The set replaces — never accompanies — a single over-budget canvas. If a user insists on "everything on one page", the A3 blueprint at the extended budget above is the ceiling; past it, deliver the set and say why.

### Loop-back, exception terminals, and the page-context panel

Three primitives that PDD-depth pages need; all live inside the existing Flowchart grammar.

**Loop-back (pagination / retry).** A decision whose "more remain" exit re-enters an earlier step — batch inserts, offset pagination, bounded retries. Route the exit **above** the main left→right row via rounded elbows, re-entering the **top edge** of the repeated node; the arc must clear every box and label it passes by the §6 connector margins — reroute rather than graze. The edge label obeys the standard budget (≤14 chars, all-caps): `YES · +BATCH`, `MORE · +OFFSET`. The exact expression (`Skip += BatchSize`) goes in the repeated node's **under-box annotation**, never in the edge label. A loop-back counts against the page's decision budget; it does not get its own budget line.

**Exception terminal (BE / SE).** A branch end that is not the process's true End: a rectangle (not an oval) named by a short mono code (`BE001`, `SE003`) with a one-line message below. **BE** (business exception) takes a solid `ink` stroke; **SE** (system exception) takes the dashed `ink @ 0.20` Optional/Async stroke — stroke style plus code prefix separate them, no dedicated red. Distinct from `EXC` in [`automation-primitives.md`](automation-primitives.md): `EXC` types an exception as an *actor/outcome* in topology diagrams and an edge kind; the BE/SE terminal is a flowchart branch terminus identified by a PDD code. BE/SE codes never appear in an activity-tag chip. Budget: **≤4 exception terminals per page**, on top of the ≤2 End ovals — more means the branches need consolidating or the page needs splitting.

**Page-context panel.** A page-level fact box — trigger mechanism, schedule, inputs consumed — that describes the page as a whole rather than pointing at one node (that job belongs to the [annotation callout](primitive-annotation.md)). It lives **inside the SVG**, in a reserved top band of the `viewBox`, exactly as the legend strip reserves the bottom band — an HTML `<div>` above the SVG would silently vanish from every `.svg`/`.png` export. Draw it as a `paper-2`-filled, hairline-bordered rect with a Geist Mono uppercase eyebrow (`TRIGGER MECHANISM`, `INPUTS`) and up to ~5 short mono lines. Budget: at most one per page; more content than that belongs in the surrounding document, not the panel.

### Revising a set

How to apply feedback to a delivered set without regenerating it wholesale:

1. **Locate, don't guess.** Map the feedback to the numbering (a phase/step reference or a quoted label) to find the exact file and node. If it doesn't resolve to one page unambiguously, ask.
2. **Edit only the touched page(s).** The HTML is the source of truth; never hand-edit an exported `.drawio` or read one back — translate the words into an HTML edit.
3. **Propagate only what must propagate.** A content edit (label fix, added step within budget) stays on its page and never touches numbering. A **structural** change (add/remove/reorder a phase or numbered process) is the only case where renumbering is allowed — and it is one atomic pass updating: overview eyebrows, the affected page's title and step-ID chips, every `↑ parent` / `CALLED FROM` link and file name pointing at the renumbered page, and the `part N of M` colophon on every page. Never leave two pages disagreeing about a number.
4. **Re-verify at set scope.** Taste gate (§9) on the touched pages, then `self_check.py --set` across the whole set — a local edit is the easiest way to silently break a cross-page link.
5. **Re-export what was regenerated.** If `.drawio`/`.png`/`.svg` existed for a touched page, regenerate them from the updated HTML ([export.md](export.md) / [export-drawio.md](export-drawio.md)). Never leave a stale export beside an updated HTML.
6. **Report what changed** — which files, what rippled, what was re-exported. Short and specific, in the spirit of the fidelity ledger.
````

- [ ] **Step 2: Extend the Anti-patterns list**

Append to the `## Anti-patterns` bullet list:

```markdown
- **"Returns to" wording on a caller link** — a static link cannot know the reader's path; the footer says `↑ parent` and `CALLED FROM`, never "returns to where you came from".
- **A reused sub-routine duplicated under a second number** — one page, one canonical number, many callers.
- **Loop-back edge label carrying the loop expression** — `YES · Skip += BatchSize` breaks the ≤14-char all-caps label budget; the expression is an under-box annotation.
- **BE/SE code in an activity-tag chip** — exception codes name terminals, not executing systems.
- **Page-context panel as an HTML `<div>`** — it must live inside the SVG viewBox or it vanishes from every export.
```

- [ ] **Step 3: Extend the Examples list**

Append to `## Examples`:

```markdown
- `assets/example-detail-set-overview.html` — detail-set overview (phases-as-nodes, forward SVG link into 2.0)
- `assets/example-detail-set-p2-catch-webhook.html` — numbered page: loop-back, BE/SE exception terminals, page-context panel, forward links to a reused sub-routine
- `assets/example-detail-set-p2.2.1-excel-readsheet.html` — reused sub-routine page (`↑ parent` + `CALLED FROM · 2.2 · 2.3` colophon)
```

- [ ] **Step 4: Verify docs consistency**

Run: `python3 scripts/verify-docs-sync.py`
Expected: PASS — the section links (`automation-primitives.md`, `primitive-annotation.md`, `export.md`, `export-drawio.md`) all resolve; no type-count drift. (The Examples entries name files that don't exist yet — verify-docs-sync only checks `.md` cross-links and gallery reachability of files **on disk**, so this passes now; Task 4 creates the files.)

- [ ] **Step 5: Commit**

```bash
git add skills/automation-design/references/type-flowchart.md
git commit -m "docs: generalize detail set to canonical hierarchy; add loop-back, BE/SE terminal, context panel, revision workflow"
```

---

### Task 3: Cross-references in sibling reference files

**Files:**
- Modify: `skills/automation-design/references/automation-primitives.md`
- Modify: `skills/automation-design/references/primitive-annotation.md`
- Modify: `skills/automation-design/references/export-drawio.md`

**Interfaces:**
- Consumes: the Task 2 section heading `### Loop-back, exception terminals, and the page-context panel` in `type-flowchart.md` (cited by name, linked as a file).
- Produces: nothing downstream depends on these lines; they are disambiguation notes.

- [ ] **Step 1: Add the EXC ↔ BE/SE disambiguation line**

In `automation-primitives.md`, in the `## Node primitives` table's following prose (directly after the `Naming:` paragraph), add:

```markdown
> **`EXC` vs. BE/SE codes.** `EXC` types an exception as an actor/outcome in topology diagrams (and `SYS EXC` / `ESCALATE` as edge labels). A PDD-style coded branch terminus inside a numbered flowchart page (`BE001`, `SE003`) is a different primitive — the **exception terminal** in [`type-flowchart.md`](type-flowchart.md) — and its codes never appear in an activity-tag chip.
```

- [ ] **Step 2: Add the callout ↔ context-panel disambiguation line**

In `primitive-annotation.md`, append to the `## Rules` bullet list:

```markdown
- A fact about the *whole page* (trigger, schedule, inputs) is not a callout — that's the **page-context panel** in [`type-flowchart.md`](type-flowchart.md), an SVG-internal top band. Callouts always point at one element.
```

- [ ] **Step 3: Document that hyperlinks don't survive drawio export**

In `export-drawio.md`, `## What does not` list, add after the "Custom arrowheads" bullet:

```markdown
- **Hyperlinks** — SVG `<a href>` navigation wraps (detail-set forward links) are dropped; the vertex is emitted without a link. Tell the user when exporting a linked detail-set page.
```

- [ ] **Step 4: Verify cross-links resolve**

Run: `python3 scripts/verify-docs-sync.py`
Expected: PASS (all three new relative links target existing files in the same directory).

- [ ] **Step 5: Commit**

```bash
git add skills/automation-design/references/automation-primitives.md skills/automation-design/references/primitive-annotation.md skills/automation-design/references/export-drawio.md
git commit -m "docs: disambiguate EXC vs BE/SE, callout vs context panel; note drawio export drops hyperlinks"
```

---

### Task 4: Example detail-set assets + gallery tabs

**Files:**
- Create: `skills/automation-design/assets/example-detail-set-overview.html`
- Create: `skills/automation-design/assets/example-detail-set-p2-catch-webhook.html`
- Create: `skills/automation-design/assets/example-detail-set-p2.2.1-excel-readsheet.html`
- Modify: `skills/automation-design/assets/index.html` (three gallery tabs)

**Interfaces:**
- Consumes: the Task 2 rules (navigation mechanisms, primitives, budgets), the Task 1 verifier (`self_check.py --set`), and the CSS/class/geometry conventions of `assets/example-process-detail.html` (use it as the base: same `:root` tokens, same `.id-text`/`.tag-text`/`.node-title`/`.node-sub`/`.annotation`/`.arrow-label`/`.legend-*` classes, same chip geometry `28×10 rx=3`, node boxes `104×48 rx=6`, terminal ovals `56×32 rx=16`, markers `#arr`/`#arr-accent`).
- Produces: the three example files the Task 2 Examples list already names, each reachable from a gallery tab.

Content is diagram authorship governed by the skill's own references (SKILL.md §5–§9, type-flowchart.md as revised); the inventories below are binding, the exact coordinates are the implementer's, on the 4px grid.

- [ ] **Step 1: Build the overview page**

`example-detail-set-overview.html` — eyebrow `Flowchart · detail set · Automation Design`, h1 `Timesheet receiver — overview`, `<svg>` ids `detail-set-overview-title`/`-desc`. Compressed phases-as-nodes form (ladder rung 3): `Start` → node `1.0 Init environment` (tag `RPA`, sublabel `temp folder · templates`, **no link** — no detail page exists for it in this mini-set, and a forward link may only exist where the target page does) → node `2.0 Catch webhook data` (tag `API`, sublabel `parse · insert bundle`) **wrapped in** `<a href="example-detail-set-p2-catch-webhook.html">` → `End`. Footer colophon (HTML, below the SVG): `part 1 of 3 · timesheet-receiver`. Legend strip: Start/End oval, process node, "boxed step links to its numbered page". Bottom-band legend per SKILL.md §6; all coords divisible by 4.

- [ ] **Step 2: Build the numbered process page (the rich one)**

`example-detail-set-p2-catch-webhook.html` — h1 `2.0 · Catch webhook data`, svg ids `detail-set-p2-title`/`-desc`. Contents, in blueprint left→right grammar:

- **Page-context panel** in a reserved top band inside the viewBox (e.g. first 72px of height): `paper-2` rect, hairline border, eyebrow `TRIGGER MECHANISM`, two mono lines (`webhook · orchestrator trigger event`, `INPUTS · raw JSON payload`).
- Flow: `Start` → `2.1 Parse payload` (tag `RPA`) → decision `Payload OK?` — NO drops to **BE terminal** `BE001` (rectangle, solid ink stroke, message line `empty webhook payload`); YES continues → `2.2 Read employee sheet` (tag `APP`, **wrapped in** `<a href="example-detail-set-p2.2.1-excel-readsheet.html">`, under-box annotation `Skip += BatchSize`) → decision `More batches?` — YES is the **loop-back**: routed above the row, re-entering the top edge of `2.2`, edge label `YES · +BATCH` (12 chars, caps); NO continues → `2.3 Read project sheet` (tag `APP`, **also wrapped in** `<a href="example-detail-set-p2.2.1-excel-readsheet.html">` — second call site) → `2.4 Insert bundle` (tag `API`) → decision `Insert OK?` — NO drops to **SE terminal** `SE001` (rectangle, dashed `ink @ 0.20` stroke, message `data service call failed`); YES → `End`.
- Budget check: 4 activities ✓ (≤8), 3 decisions ✓ (≤3, loop-back counted), 2 exception terminals ✓ (≤4), 1 Start, 1 End ✓.
- Focal accent: the loop-back arc and its decision (the batching mechanic is this page's story) — nothing else accented.
- Footer colophon: `part 2 of 3 · timesheet-receiver` · `↑ overview` linking `example-detail-set-overview.html`.
- Legend: step, decision, BE terminal (solid), SE terminal (dashed), loop-back arc, "linked step opens its sub-routine page".

- [ ] **Step 3: Build the reused sub-routine page**

`example-detail-set-p2.2.1-excel-readsheet.html` — h1 `2.2.1 · Excel read sheet`, svg ids `detail-set-p221-title`/`-desc`. Flow: `Start` → `2.2.1.1 Validate arguments` (tag `RPA`) → decision `Workbook exists?` — NO → **SE terminal** `SE002` (dashed, `workbook not found`); YES → `2.2.1.2 Read range` (tag `APP`, sublabel `sheet → DataTable`) → `2.2.1.3 Validate output` (tag `RPA`) → `End` (plain — sub-routine return semantics live in the colophon, ovals are never wrapped). Footer colophon: `part 3 of 3 · timesheet-receiver` · `↑ 2.0 · catch webhook data` linking the p2 file · `CALLED FROM · 2.2 · 2.3` with both entries linking `example-detail-set-p2-catch-webhook.html`.

- [ ] **Step 4: Add the gallery tabs**

In `assets/index.html`, after the existing `data-type="process-detail"` button, add three buttons copying that button's exact inner markup shape:

```html
        <button class="tab" data-type="detail-set-overview" data-single>
          Detail set · overview
        </button>
        <button class="tab" data-type="detail-set-p2-catch-webhook" data-single>
          Detail set · 2.0 page
        </button>
        <button class="tab" data-type="detail-set-p2.2.1-excel-readsheet" data-single>
          Detail set · 2.2.1 sub-routine
        </button>
```

(Adjust the literal inner text/markup to match the sibling buttons' structure exactly — including any icon/label spans they carry.)

- [ ] **Step 5: Run every relevant gate**

```bash
python3 skills/automation-design/scripts/self_check.py skills/automation-design/assets/example-detail-set-overview.html skills/automation-design/assets/example-detail-set-p2-catch-webhook.html skills/automation-design/assets/example-detail-set-p2.2.1-excel-readsheet.html
python3 skills/automation-design/scripts/self_check.py --set skills/automation-design/assets/example-detail-set-overview.html
python3 scripts/verify-geometry.py --all
python3 scripts/lint-skin.py --all --baseline
python3 scripts/test-lint-a11y.py
python3 scripts/verify-docs-sync.py
```

Expected: all PASS. If `lint-skin` or `verify-geometry` flags a new file, fix the file — never the baseline.

- [ ] **Step 6: Visual check**

Open each file in a browser (or via Playwright screenshot) and verify: the loop-back arc is traceable and clears all boxes; the context panel reads as part of the figure; clicking `2.0` on the overview opens the p2 page; `CALLED FROM` links work; nothing overlaps. Fix on the spot.

- [ ] **Step 7: Commit**

```bash
git add skills/automation-design/assets/example-detail-set-overview.html skills/automation-design/assets/example-detail-set-p2-catch-webhook.html "skills/automation-design/assets/example-detail-set-p2.2.1-excel-readsheet.html" skills/automation-design/assets/index.html
git commit -m "feat: add linked detail-set example assets (overview, numbered page, reused sub-routine)"
```

---

### Task 5: Plugin version bump + full verification sweep

**Files:**
- Modify: `.claude-plugin/plugin.json` and marketplace manifests (via `scripts/bump-plugin-version.py` — never by hand)

**Interfaces:**
- Consumes: everything above committed.
- Produces: a CI-green tree.

- [ ] **Step 1: Bump the plugin version**

Run `python3 scripts/bump-plugin-version.py --help` to confirm invocation, then bump the **minor** version (new capability, no breaking change). Verify the gate passes against the pre-change base:

```bash
git log --oneline -8   # note the SHA before Task 1's commit
python3 scripts/verify-plugin-package.py <that-sha>
python3 scripts/test-plugin-package.py
```

Expected: both PASS.

- [ ] **Step 2: Run the full CI-equivalent sweep**

```bash
python3 scripts/test-lint-a11y.py && \
python3 scripts/verify-semantic-motion.py --markdown-only && \
python3 scripts/verify-semantic-motion.py --example-only && \
python3 scripts/verify-motion.py --shipped && \
python3 scripts/lint-skin.py --all --baseline && \
python3 scripts/verify-sequence-oauth.py && \
python3 scripts/verify-drawio-import.py && \
python3 scripts/verify-mermaid-import.py && \
python3 scripts/test-verify-motion.py && \
python3 scripts/verify-docs-sync.py && \
python3 scripts/test-verify-docs-sync.py && \
python3 scripts/test-self-check.py && \
python3 scripts/verify-geometry.py --all && \
python3 scripts/test-verify-geometry.py && \
python3 scripts/test-mxgraph-emit.py && \
echo ALL GREEN
```

Expected: `ALL GREEN`.

- [ ] **Step 3: Commit**

```bash
git add -A
git status   # review: only version manifests should be staged here
git commit -m "chore: bump plugin version for detail-set hierarchy release"
```

---

## Self-review notes

- Spec §2.1–2.6 → Task 2; spec §4 self_check requirement → Task 1; spec §4 export-drawio doc line → Task 3; spec §4 example assets → Task 4; spec §6 verification impact → Tasks 4–5. Spec §4's automation-primitives/primitive-annotation cross-refs → Task 3. No spec requirement is unowned.
- Non-goals respected: no task touches `mxgraph_emit.py`, `drawio_extract.py`, `import-drawio.md`, `style-guide.md`, or the type/pattern counters.
- Type consistency: `verify_set(overview: Path) -> list[str]` is defined in Task 1 and cited identically in Tasks 2 (doc text) and 4 (gate command). File names are identical across Tasks 2 (Examples list), 4 (creation), and the gallery `data-type` values (`example-<type>.html` convention).
