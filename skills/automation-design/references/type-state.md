# State Machine

**Best for:** finite state logic — order status, auth state, connection lifecycle, form wizard, job queue status.

## Layout conventions
- States are rounded rectangles (`rx=8`), labeled in Geist.
- **Start**: filled ink dot (`r=6`). **End**: ringed dot (outer `r=8` outline, inner filled `r=5`).
- Transitions: curved arrows labeled in Geist Mono as `event [guard] / action` (omit sections you don't need).
- Self-loops curve above the state.
- Orient along the dominant flow direction (left→right or top→down); rearrange before crossing transitions.
- Coral on the state the reader should notice — typically the error state, or "happy completion".

## Screen-states flavor (application navigation)

Used by the **Application card** pattern ([semantic-patterns.md §20](semantic-patterns.md)) for an app's navigation map: screens are states, UI events are transitions, roles are guards — the standard `event [guard] / action` notation. Conventions on top of the base grammar:

- **The initial dot is the post-sign-in entry.** The identity provider's hosted sign-in is not a state of the app; the transition label carries it (`SIGN IN · IDP`).
- **State-ID chips.** Each screen carries a `SCREEN` or `MODAL` tag plus a state-ID chip (`2.0`, `2.1`) — the same IDs the screen contract and prose reference.
- **Modals are transient states**, drawn with the dashed Optional/Async treatment.
- **Every state is leavable.** Returns are explicit (`CANCEL`, `BACK`); an async confirmation is its own pair of transitions (`CONFIRM [AUTH] / ENQUEUE`, then `ACK QUEUED` to the target — failure stays in place).
- **Data bindings live in state sublabels** (`Invoices · status = pending`) — the contract page owns the full operation list.

Drawn only when the app has ≥2 meaningfully connected states; a single-screen app doesn't get one. Budget: the type's base ≤6 states / ≤10 transitions.

## Anti-patterns
- More transitions than states × 2 → likely two state machines.
- "From any state" transitions drawn from every state — use a single annotation (`* → Error on timeout`) instead.
- Unlabeled transitions (the whole point is *what triggers this*).
- **A terminal node duplicating an existing state** (screen-states flavor) — transition back to the state, don't redraw it.
- **A screen with no exit** — if the user can reach it, they can leave it.

## Examples
- `assets/example-state.html` — minimal light
- `assets/example-state-dark.html` — minimal dark
- `assets/example-state-full.html` — full editorial
- `assets/example-screen-states.html` — screen-states flavor (screens as states, guards, async ack, transient modals)
