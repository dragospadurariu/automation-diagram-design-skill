# Database schema

**Best for:** the physical database schema: real tables, SQL types, constraints, indexes, schema namespaces, and foreign keys anchored from one column row to another.

**Not for:** conceptual domain modeling or a generic data-flow view. If the question is what moves between systems, use **Data flow**. Use database schema when `uuid` versus `text`, `PK/FK/UQ/NN`, or `ON DELETE` behavior is load-bearing.

## Layout grammar

### Table boxes

- Header: `schema.table` in Geist 12px/600 plus a rectangular `TABLE` tag (`rx=2`).
- Rows: fixed 24px height; name left in Geist 12px, SQL type right in Geist Mono 9px.
- Constraint chips sit between name and type: `PK`, `FK`, `UQ`, `NN`, each Geist Mono 8px with `rx=2`.
- Alternate rows may use `ink @ 0.02`; keep contrast quiet.
- If columns are omitted, end with `+ N more columns`. Never truncate silently.
- Optional indexes live in a separated compartment labelled `INDEXES`.

### Column-level foreign keys

- Anchor each connector to the vertical center of the exact source and target column rows.
- Draw connectors before table boxes and route them orthogonally.
- Label destructive behavior explicitly: `ON DELETE CASCADE`, `SET NULL`, or `RESTRICT`.
- Use `accent` only for the one relationship under review; ordinary foreign keys use `muted`.
- Put every label on an opaque `paper` mask with a 6–10px gap from the line.
- If routes cross, add a bridge or offset the paths. Two foreign keys may not share one track.

### Schema groups

Use a dashed `rule-solid` container when a non-default namespace materially matters. Place the group before connectors and tables in SVG order so tables remain legible.

## Complexity budget

- 5 tables per page by default; 7 only when tables are small.
- 6 visible columns per table; summarize the remainder.
- 8 foreign keys per page.
- 2 index names per table.
- 1 focal relationship.

Split a larger model by bounded context or schema namespace and add a small overview page.

## Legend

Show only primitives used: table, schema group, constraint chip, ordinary foreign key, and focal/destructive foreign key.

## Anti-patterns

- Box-to-box relationship lines that hide the participating columns.
- Omitting SQL types or delete behavior when those facts exist.
- Crowding every production column and index into one page.
- Using accent on every foreign key.
- Drawing connectors over column text or through another table.

## Shipped examples

- `assets/example-db-schema.html` — minimal light.
- `assets/example-db-schema-dark.html` — minimal dark.
- `assets/example-db-schema-full.html` — full editorial frame.
