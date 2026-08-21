# Contributing to Automation Design

Thanks for wanting to contribute — this project only gets better with more eyes on it.

Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) first. All contributions are expected to keep the community welcoming.

---

## What this project is

Automation Design is an agent skill (Claude Code, Codex, Pi) that produces editorial-quality diagrams as self-contained HTML files. The repo is documentation-first: `skills/automation-design/SKILL.md` is the index, each of the 11 visual types has its own reference file, and the extractor scripts in `skills/automation-design/scripts/` turn draw.io and Mermaid sources into a structured IR.

See [README.md](README.md) for the full picture, including the design system and the import/export flows.

---

## Before you start

- **Create an issue first** for anything non-trivial (new type, behavior change, import grammar work). Small fixes and docs can go straight to a PR.
- **Work on a branch** — never commit directly to `main`.
- **Keep the scope tight.** One PR = one concern. Mixing a new diagram type with a docs rewrite makes review slow.
- **Python 3.10+ is required** for the development scripts (CI runs 3.11 and 3.12 across Linux, Windows, and macOS).

---

## Validation gates

Every validation gate below must pass before a PR is ready. They also run automatically as GitHub Actions CI (`.github/workflows/ci.yml`).

Every PR changes the distributed plugin package, including documentation- and CI-only PRs. Increment both native manifests together before opening or updating a PR:

```bash
python3 scripts/bump-plugin-version.py          # patch (default)
python3 scripts/bump-plugin-version.py --minor  # minor release
python3 scripts/bump-plugin-version.py --major  # major release
```

The helper refuses to run if the Claude and Codex versions already differ. If another release lands on `main` first, rebase and bump again so your version remains greater than the new base.

| What it checks | Command |
|---|---|
| Plugin bump helper and adversarial package cases | `python3 scripts/test-plugin-package.py` |
| Synchronized, increasing versions; valid marketplace paths; packaged skill | `python3 scripts/verify-plugin-package.py origin/main` |

While the base ref still carries the pre-fork plugin name, the version-increase half of that gate is **waived** — version lineage restarts at a rename, so `2.5.0 → 0.1.0` is legitimate. The waiver prints a `WAIVED …` line rather than passing quietly, and it lapses by itself once the rename has landed on the base branch; the semver and Claude/Codex-match checks apply throughout.
| Claude marketplace and plugin schema, with warnings treated as errors | `claude plugin validate . --strict` |
| Accessible SVG contract (unit tests for the a11y linter) | `python3 scripts/test-lint-a11y.py` |
| Semantic-pattern routing | `python3 scripts/verify-semantic-motion.py --markdown-only` |
| Animated-example structure and accessibility | `python3 scripts/verify-semantic-motion.py --example-only` |
| Skin conformance of every example and template (colors, fonts, a11y, assets, scripts) | `python3 scripts/lint-skin.py --all --baseline` |
| A single file, e.g. a new example | `python3 scripts/lint-skin.py skills/automation-design/assets/example-my-type.html` |
| Sequence-doc consistency (ATL fragments, budgets) | `python3 scripts/verify-sequence-oauth.py` |
| draw.io import path (real extractor vs fixtures + docs sync) | `python3 scripts/verify-drawio-import.py` |
| Mermaid import path (grammars, adversarial input, caps, docs sync) | `python3 scripts/verify-mermaid-import.py` |
| Optional motion contract (fallbacks, controls, budgets, determinism) | `python3 scripts/test-verify-motion.py` |
| Every shipped motion template/example | `python3 scripts/verify-motion.py --shipped` |
| Docs/routing sync (description hooks, gallery, README tree, SKILL.md reference links, references/ cross-links, profile surfaces) | `python3 scripts/verify-docs-sync.py && python3 scripts/test-verify-docs-sync.py` |
| Packaged output self-check behaves (pass + adversarial cases) | `python3 scripts/test-self-check.py` |
| Diagram geometry: masks clear of nodes and strokes, no overlapping connectors, no strokes buried under nodes, every arrowhead lands on a border | `python3 scripts/verify-geometry.py --all` |
| Geometry checker behaves (pass + adversarial cases) | `python3 scripts/test-verify-geometry.py` |
| Generated icon assets are up to date (`icons.html`, `primitive-icons.md`) | `python3 scripts/build-icons.py` then `git diff --exit-code` on the two generated files |

The semantic-pattern gate also caps `skills/automation-design/SKILL.md` at 40,000 bytes so the installed skill remains practical to load. If that gate fails, reduce duplication or move detail into a routed reference; do not remove routing vocabulary from frontmatter.

Run them all at once before pushing:

```bash
python3 scripts/test-plugin-package.py \
  && python3 scripts/verify-plugin-package.py origin/main \
  && claude plugin validate . --strict \
  && python3 scripts/test-lint-a11y.py \
  && python3 scripts/verify-semantic-motion.py --markdown-only \
  && python3 scripts/verify-semantic-motion.py --example-only \
  && python3 scripts/verify-motion.py --shipped \
  && python3 scripts/lint-skin.py --all --baseline \
  && python3 scripts/verify-sequence-oauth.py \
  && python3 scripts/verify-drawio-import.py \
  && python3 scripts/verify-mermaid-import.py \
  && python3 scripts/test-verify-motion.py \
  && python3 scripts/verify-docs-sync.py \
  && python3 scripts/test-verify-docs-sync.py \
  && python3 scripts/test-self-check.py \
  && python3 scripts/verify-geometry.py --all \
  && python3 scripts/test-verify-geometry.py
```

### If a gate fails

- **`verify-plugin-package.py`:** run the bump helper if the versions did not increase. If packaging validation fails, keep both marketplaces pointed at the repository root and keep the shared skill at `skills/automation-design/SKILL.md`.
- **`lint-skin.py`:** the failure message names the file, line, and category (`color`, `font-family`, `a11y`, `external-asset`, `pure-black`, `script`). Colors must come from the palette in `skills/automation-design/references/style-guide.md`; fonts from the allowed list; diagrams must satisfy the accessible SVG contract (see below). The linter also requires the SHA-pinned controller from `template-motion.html` verbatim and rejects remote resources, CSS `@import`, non-fragment CSS `url()`, event handlers, `srcdoc`, executable URLs, and extra scripts.
- **`verify-*.py`:** the extractor's real behavior no longer matches its fixture or the documentation, or the reference/command/prompt wiring drifted. Fix the source of truth — do not widen a test to avoid a failure.
- **`verify-geometry.py`:** the message names the defect. *Mask clipped by a node*: move the label to a free segment of its connector — do not shrink the mask to sneak under the check. *Mask on / too close to a stroke*: keep a ≥6px gap between the mask rect and every connector (SKILL.md §6 rule 2). *Parallel runs closer than 12px*: re-route one connector or fan the attach points (§6 rules 3–4). *Stroke buried under a node*: route around it through open canvas. *Arrowhead in open canvas*: end the path exactly on the target's border, a lifeline, or an activation bar (§6 rule 7) — decision diamonds must be `<polygon>` (not `<path>`) so the checker can see them as landing surfaces.
- **Icon assets:** you changed `scripts/vendor/icons/` or `scripts/build-icons.py` and the generated files went stale. Rerun `python3 scripts/build-icons.py` and commit the regenerated files.

Do **not** add a file to `scripts/lint-skin-baseline.txt` to get your example through. The baseline exists only for legacy pre-2.0 examples that legitimately predate the current skin, and it still receives a11y checks.

---

## The accessible SVG contract (a11y)

Every diagram `<svg>` must satisfy the contract enforced by the linter:

1. `role="img"` and `aria-labelledby` naming the `<title>` **and** `<desc>`.
2. `<title>` is the **first child** of `<svg>` (before `<defs>`).
3. IDs are prefixed per diagram and variant: `<slug>-title` / `<slug>-desc` — for `example-loop-dark.html` the slug is `loop-dark`, so the IDs are `loop-dark-title` / `loop-dark-desc`. Bare `title`/`desc` IDs and duplicate IDs are rejected.
4. `<title>` is the short subject name (≈ the `<h1>`, ≤ 60 chars); `<desc>` is one sentence describing the *content*, not the geometry.
5. Purely decorative SVGs (`aria-hidden="true"`) are exempt.

The contract lives in `scripts/lint-skin.py` (`lint_accessible_svgs`) and is unit-tested by `scripts/test-lint-a11y.py`. When in doubt, pattern-match an existing example.

---

## Working on examples (diagrams)

Every diagram type ships three variants: minimal light (`example-<type>.html`), minimal dark (`example-<type>-dark.html`), and full editorial (`example-<type>-full.html`).

1. Copy the closest template (`skills/automation-design/assets/template.html`, `template-dark.html`, or `template-full.html`).
2. Load the matching `references/type-<name>.md` and follow its layout conventions.
3. Replace the eyebrow, h1, and SVG body; replace the `[diagram-slug]` placeholders with your file's slug and keep the `<title>`/`<desc>` slots filled.
4. Run the taste gate in `SKILL.md` §9, then the linter:

```bash
python3 scripts/lint-skin.py skills/automation-design/assets/example-my-type.html
```

New examples should be added to the gallery (`assets/index.html`) so they stay browsable.

Motion is opt-in. Start from `skills/automation-design/assets/template-motion.html`, follow `references/animation.md`, and run `python3 scripts/verify-motion.py <file>` plus `python3 scripts/test-verify-motion.py`. A motion file must preserve complete no-JavaScript, reduced-motion, print, screenshot, and export states. Keep the controller byte-for-byte identical to the template; changes require updating the canonical template, example, documentation, and adversarial tests together.

## Design decisions (ADRs)

Settled policies live as short records in `docs/adr/` — one pinned motion controller, semantic patterns never expanding the visual-type taxonomy, the reveal-only autoplay rule, the SKILL.md byte cap with its trigger-rich description requirement, and geometric label placement being verified rather than reviewed. Read the relevant ADR before proposing a change that touches one; when a PR settles a new policy, add an ADR in the same PR.

## Adding a new diagram type

1. Write `skills/automation-design/references/type-<name>.md` — layout conventions, anti-patterns, and a worked pattern for that type. Mirror an existing reference's structure.
2. Add the row to the selection table in `skills/automation-design/SKILL.md` §3 **and** the type's name to the frontmatter `description` — `verify-docs-sync.py` fails if the description loses or lacks a type's lexical hook.
3. Add the three example variants (see above) and register them in the gallery (`assets/index.html`) — `verify-docs-sync.py` fails on any shipped example the gallery can't reach.
4. Bump the two type counters together: the row count asserted in `verify-docs-sync.py` and in `verify-semantic-motion.py`, plus the `### Visual-type guide (N)` heading they anchor on. They deliberately hard-assert the current count, so step 2 alone leaves the suite red.
5. Amend `docs/adr/0002` in the same PR. Those counters are that record's enforcement, so moving them without amending it makes the test the authority instead of the decision. Say why the new type is a layout grammar no existing type provides — that is the only accepted reason, and ADR 0007 adds a second bar: it must serve the automation scope.
6. Run the full gate suite — new examples are linted automatically by `--all`.

## Changing the icon set

Icons are generated, never hand-edited:

1. Add or replace the source SVG in `scripts/vendor/icons/<source>/` (`tabler/`, `simple/`, …). Keep license provenance in `THIRD_PARTY_LICENSES.md` accurate.
2. Regenerate and verify:

```bash
python3 scripts/build-icons.py
git diff --exit-code -- skills/automation-design/assets/icons.html skills/automation-design/references/primitive-icons.md
```

## Touching the import paths

- draw.io: `skills/automation-design/scripts/drawio_extract.py` — must pass `scripts/verify-drawio-import.py`, which drives the extractor against `scripts/fixtures/sample-architecture.drawio` in all four container formats (raw XML, deflate+base64, PNG-embedded, SVG-embedded).
- Mermaid: `skills/automation-design/scripts/mermaid_extract.py` — must pass `scripts/verify-mermaid-import.py`, which covers every supported grammar, multi-block Markdown, adversarial labels, trust-boundary behavior, resource caps, and named failures.

Both scripts treat their input as **untrusted data** — they never render, fetch, or execute source content. Keep it that way. If you add a grammar or a new security boundary, extend the corresponding verifier with a fixture before merging.

Documentation and wiring must stay in sync: the import references, `SKILL.md` §11, the slash commands in `commands/`, and the Pi prompt templates in `prompts/` each describe the same flows. The verifiers check this — keep both sides updated in one PR.

## Documentation

Most of this repo *is* documentation. When behavior changes, update the affected reference files and the README in the same PR. Loose ends here are what the verifiers and reviewers will catch.

---

## Commit and PR conventions

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/): `type(scope): summary`, e.g. `fix(import): support current Mermaid syntax`, `ci: verify Mermaid imports`, `docs(onboarding): clarify the URL flow`. Keep summaries short and imperative.

A good PR:

- has a clear title and a description that says *what* changed and *why*;
- mentions how you tested it (which gates you ran);
- keeps generated and source files consistent (extractor + verifier + reference + command in one change);
- is rebased on `main` and green on CI.

## Questions?

Open a discussion or comment on the relevant issue. If it's about security, use the private reporting path in [SECURITY.md](SECURITY.md).
