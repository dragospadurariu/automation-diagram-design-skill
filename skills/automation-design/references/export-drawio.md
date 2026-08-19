# Export to draw.io

Convert a generated diagram HTML file into a native, editable `.drawio` next to it. **Manual only — never run unprompted.**

## Trigger

Load this file when:

- The user invokes `/automation-design:export-diagram <html-file> --format=drawio`.
- The user asks in natural language for a draw.io / diagrams.net version of a generated diagram. Typical phrasings:
  - "give me this as a drawio file"
  - "export to draw.io so I can edit it"
  - "I want to keep working on this in diagrams.net"
  - "make it editable"

The import direction — redrawing an *existing* `.drawio` in this skill's design system — is the opposite flow and lives in [`import-drawio.md`](import-drawio.md). Do not confuse the two: import consumes draw.io files, this reference produces them.

## What this is for

The HTML remains the source of truth and the only artifact the taste gate (SKILL.md §9) is written against. The `.drawio` is a **hand-off**: the person who receives it will drag nodes, reword labels, and extend the diagram in the draw.io editor. Everything the emitter does is in service of that — one cell per card, badges parented to their card, connectors bound to endpoints so they re-route when a node moves.

## Procedure

Run the packaged emitter — never hand-author mxGraphModel XML:

```bash
python3 <skill-dir>/scripts/mxgraph_emit.py <diagram.html> [--out PATH] [--report]
```

- Default output is `<diagram>.drawio` next to the source; `--out` overrides.
- `--report` prints the delta ledger — always pass it and relay the ledger to the user.
- Exit codes: `0` ok, `2` unreadable input or no `<svg>` block. Surface the error verbatim and stop.

The emitter reads the inline SVG and the page's CSS cascade, classifies every element (canvas / lane band / node / badge / label mask / chip / connector), and writes uncompressed `<mxfile>` XML. Geometry is copied verbatim, so the layout matches the HTML by construction — no layout engine runs and none is needed.

## What survives translation

| Source | draw.io |
|---|---|
| Node cards, pills, diamonds, circles | one vertex each — `rounded`, `rhombus`, `ellipse` |
| Badges and chips on a card | child cells parented to the card; they move with it |
| Connectors with elbows | edges with waypoints, bound to their endpoints |
| Arrow annotations on a paper mask | the edge's own label with `labelBackgroundColor` |
| `rgba()` tokens | `fillOpacity` / `strokeOpacity` — alpha survives |
| Brand webfonts | `fontSource` per cell (loads Google Fonts in the editor) |
| Dashed strokes, `opacity`, letter-spacing | `dashPattern`, `opacity`, inline CSS in the HTML label |
| Light/dark tokens | resolved to literals; the page background is set on the model |

## What does not

- **The editorial wrapper** — eyebrow, headline, summary cards. Diagram-only, same rule as [`export.md`](export.md).
- **Pattern fills** — the dotted paper texture has no draw.io equivalent; a page has a background color, not a background pattern.
- **Motion** — `data-motion-*` steps flatten to the final static frame.
- **Custom arrowheads** — the 6×6 marker becomes `blockThin`; close, not identical.

Every deliberate drop is counted in the delta ledger the emitter prints. A source element missing from the output *without* a ledger line is a bug — report it, don't shrug.

## Edge cases

- **Source is `assets/index.html`** (the gallery, many SVGs in one file) → refuse and ask which specific diagram file.
- **Source has no `<svg>` block** → the emitter exits 2; relay its message.
- **User asks for `.drawio` of a diagram that doesn't exist yet** → generate the HTML first (it is the artifact the taste gate runs against), then emit.

## Verification

`scripts/test-mxgraph-emit.py` at the repo root regression-tests the emitter against every shipped example and every bug class found during its audit. Run it after any change to the emitter.
