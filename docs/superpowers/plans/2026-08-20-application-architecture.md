# Application Architecture Family Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the application diagram family — pattern 20 (Application card + conditional screen contract), the screen-states State-machine flavor, the conditional runtime-topology annex, application vocabulary, four example assets, and a README refresh with screenshots.

**Architecture:** Same shape as the two prior cycles (detail-set, agent): reference docs first, counters + ADR together, assets hardened from the thrice-reviewed mockups in `experiments/app-mockups/`, README last, full sweep, squash-merge.

**Tech Stack:** Markdown references, SVG-in-HTML assets, Playwright screenshots, Python verifier suite.

**Spec:** `docs/superpowers/specs/2026-08-20-application-architecture-design.md`

## Global Constraints

- Branch `feature/application-architecture`; main gets one squash-merge.
- Counters (19→20) move in the same commit as the ADR 0002 amendment.
- The family pages are **defaults with selection conditions, never mandatory** — the spec's ownership/conditions table is copied into the pattern text.
- Screen-contract budget: 1 screen, ≤3 data deps, ≤3 events, ≤2 downstream steps, 1 async boundary; non-composable, total wins.
- Architecture zones stay ≤3; browser is an external node.
- Asset slugs = file stems; no `href="#"`; plain-text colophons; fix the runtime mock's ETL-label/node overlap during hardening.
- Screenshot convention: Playwright @2, screenshot the `<svg>` element only, into `docs/screenshots/<slug>.png`.
- Known trap: `build-icons.py` EOL-only diffs — restore, never commit.

---

### Task 1: Reference docs (pattern 20, vocabulary, flavors, annex notes)

**Files:** `semantic-patterns.md`, `automation-primitives.md`, `type-state.md`, `type-architecture.md`, `type-flowchart.md`, `SKILL.md`, 3 manifest slots, `verify-semantic-motion.py`, ADR 0002.

- [ ] Write §20 in `semantic-patterns.md` from spec §2.1 (selection triggers, main view + drill-down variant with the qualification list, conditions/ownership table, budgets, anti-patterns, static fallback, nearest type = Architecture) + routing row + intro 8–20.
- [ ] Add the Application vocabulary block to `automation-primitives.md` (spec §2.5) and bump its "rows 8–19" mention to 8–20.
- [ ] Add the screen-states flavor to `type-state.md` (spec §2.2) + example entry `assets/example-screen-states.html`.
- [ ] Add the runtime-topology conditional-annex note to `type-architecture.md` (spec §2.3) + example entries for `example-app-card.html`, `example-screen-contract.html`, `example-runtime-topology.html`.
- [ ] Generalize the annex sentence in `type-flowchart.md` (spec §2.4).
- [ ] SKILL.md routing row + description hooks; paste the description verbatim into `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.codex-plugin/plugin.json` (`description` + `longDescription`).
- [ ] `PATTERN_NAMES` += `"Application card"`; OK string → 20; ADR 0002 amendment (same commit).
- [ ] Verify: `verify-semantic-motion.py --markdown-only` (20 patterns), `verify-docs-sync.py`. Commit.

### Task 2: Example assets + gallery

**Files:** create `assets/example-app-card.html`, `example-screen-states.html`, `example-screen-contract.html`, `example-runtime-topology.html`; modify `assets/index.html`.

- [ ] Harden each from its mockup (`experiments/app-mockups/mock-app-card.html`, `mock-screen-flow.html`, `mock-screen-card.html`, `mock-tech-architecture.html`): retitle (drop MOCKUP), slug-correct title/desc IDs, plain colophons, fix the ETL/QUERY label overlaps in the runtime file (shift masks clear of node edges), keep everything the reviews validated.
- [ ] Four gallery tabs (13i–13l, `data-single`), following the existing button markup.
- [ ] Gates: `self_check.py` on all four, `verify-geometry.py --all`, `lint-skin.py --all --baseline`, `test-lint-a11y.py`, `verify-docs-sync.py`. Visual check via local server + Playwright. Commit.

### Task 3: README refresh + screenshots

**Files:** `README.md`; create 6 PNGs in `docs/screenshots/`.

- [ ] Generate screenshots (Playwright @2, `<svg>` only) for: `agent-card`, `agent-card-conversational` (0.3.0 assets, missed then), `app-card`, `screen-states`, `screen-contract`, `runtime-topology`.
- [ ] README: fix stale counts (`18 semantic patterns` → `20`, `11 automation patterns` → `13`, and the pattern list sentence gains `agent card` and `application card`); add an "Agents and applications" section after the three-altitudes section with the six screenshots and one-line captions + asset links, following the existing image+caption idiom.
- [ ] `verify-docs-sync.py` (README tree unchanged; links resolve). Commit.

### Task 4: Version bump + sweep + squash-merge

- [ ] `bump-plugin-version.py --minor` (0.4.0); `test-plugin-package.py`; `verify-plugin-package.py origin/main`.
- [ ] Full CI-equivalent sweep (same 15-command chain as prior cycles) → `ALL GREEN`. Commit bump.
- [ ] `git checkout main && git merge --squash feature/application-architecture`, single release commit, push, delete branch.

## Self-review

Spec §2.1→T1+T2; §2.2→T1+T2; §2.3→T1+T2; §2.4–2.5→T1; §3 README/screenshots→T3; §5→T2/T4. Names consistent: pattern `Application card`; slugs `app-card`, `screen-states`, `screen-contract`, `runtime-topology` everywhere.
