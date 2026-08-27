# Process-state profiles

Process profiles describe **which operational state is being documented**. They are orthogonal to both semantic pattern and visual type: choose the behavior to explain, choose the layout grammar, then apply a profile only when the distinction between current, future, or migration state matters.

Do not create a new visual type merely because a process is AS-IS or TO-BE. The selected type still owns its axis, connector grammar, geometry, and complexity budget:

- [Process](type-process.md) when step sequence, responsible actor, input/output, and tool must all remain visible.
- [Swimlane](type-swimlane.md) when ownership and cross-lane handoffs dominate.
- [Flowchart](type-flowchart.md) when branching and decision logic dominate.
- [Sequence](type-sequence.md) when message order, waits, or runtime interaction dominate.

[`../taxonomy.json`](../taxonomy.json) owns the stable profile IDs and labels. This reference owns their evidence and drawing contracts.

## Stable profiles

| Stable profile ID | Label | Meaning |
|---|---|---|
| `profile.as-is` | `AS-IS` | Observed current execution, including unknowns, manual work, waits, rework, and exceptions without invented improvements. |
| `profile.to-be` | `TO-BE` | Intended future execution, with proposed behavior and assumptions distinguished from approved requirements. |
| `profile.transition` | `TRANSITION` | Migration path from current to future execution, with temporary states, cutovers, owners, and retirement points. |

Omit the profile when the diagram is timeless or the state distinction does not change the reader's decision. Never silently default an explicitly current-state request to TO-BE.

## Input contract

Add these optional fields beside the selected type's normal inputs:

```yaml
process_profile: as-is             # as-is | to-be | transition
profile_context:
  status: draft                    # draft | validated | approved
  effective_or_observed_on: null   # ISO date or explicit UNKNOWN
  sources:                         # 1..3 concise provenance labels
    - "process-owner walkthrough"
  measures:
    volume: unknown
    work_time: unknown
    wait_time: unknown
    rework: unknown
```

Use `unknown`, never `0`, an empty string, or an invented estimate. A missing fact is part of the process evidence.

## Shared profile strip

When a profile is present, reserve a compact evidence strip **inside the SVG**, above the selected type's normal header. It must survive SVG/PNG export.

Required fields:

- profile label and validation status;
- observation/effective date, or `UNKNOWN`;
- source/provenance;
- scope boundary;
- the most decision-relevant missing or measured quantities.

Geometry modifier for parametric types:

```text
profile_h       = 32 if process_profile else 0
normal_header_y = profile_h
content_y       = profile_h + type_header_h
viewBox_h       = profile_h + original_viewBox_h
```

Shift the type's existing header, lanes, nodes, connectors, and legend down by `profile_h`; do not compress the type to make room. The profile strip uses `paper-2`, `rule`, and mono 6–8px labels. It is evidence, not a decorative banner.

## AS-IS contract

An AS-IS diagram records what happens now, including inconvenient behavior. It is not the place to repair the process.

Required:

- one source and observation date/status in the profile strip;
- every active step assigned to exactly one performer lane;
- system class visible where it changes interpretation (`RPA`, `FLOW`, `MODEL`, `AGENT`, `HUMAN`, `API`, `APP`);
- manual handoffs, queues, waits, loops, rework, exceptions, and abandonment paths shown when present;
- known measures with units; unknown measures written as `UNKNOWN` or `NOT PROVIDED`;
- distinct terminal outcomes when success and escalation do not mean the same thing;
- inferred content marked `INFERRED` until validated by a process owner.

Recommended measures, shown only when known: transaction volume, frequency, work time, wait time, first-pass yield, exception rate, and rework count.

Use `accent` for the single handoff or automated path the reader must inspect. Use `danger` only for real exception/failure paths. Human work is not automatically an error and must not become red merely because it is manual.

**Anti-patterns:** cleaning up the route to look efficient; replacing a current manual step with proposed automation; hiding an undocumented branch; treating missing measures as zero; mixing actors, departments, and applications as lanes without stating that the lane axis is `PERFORMER`; a generic End that erases materially different outcomes.

## TO-BE contract

A TO-BE diagram states intended behavior. It may propose change, but must not present proposals as already operational.

Required:

- approval state and effective target date, or `UNKNOWN`;
- assumptions and unresolved decisions named in the profile strip or adjacent document;
- new, changed, and retired responsibilities made explicit;
- controls, exception handling, and human fallback shown alongside the happy path;
- target measures labeled `TARGET`, never mixed with observed AS-IS values.

When comparing AS-IS and TO-BE, create two matched figures with the same scope, lane axis, scale, and terminology. Do not overlay both states on one ordinary process canvas.

## TRANSITION contract

Use TRANSITION only when temporary coexistence and migration sequencing are the story. A transition figure is not a vague midpoint between two polished diagrams.

Required:

- current, temporary, and target states or phases visibly distinguished with text;
- cutover gates, owners, dependencies, rollback/abort conditions, and retirement points;
- temporary duplicate work and reconciliation paths shown rather than simplified away;
- each milestone tied to an exit condition, not merely a date;
- measures labeled `BASELINE`, `INTERIM`, or `TARGET`.

If the transition contains more than five milestones or three concurrent operating modes, use an overview plus detail pages. Route a deployment chronology to Sequence when time ordering is load-bearing.

## Validation questions

Before delivery, ask:

1. Does the profile label match the claims actually drawn?
2. Can every AS-IS claim be traced to a source, observation, or explicit inference?
3. Are unknowns visible rather than silently completed?
4. Are success, exception, escalation, and abandonment outcomes distinct?
5. Would a reviewer mistake a proposal for observed behavior?
6. Does the selected visual type still own the layout, with the profile acting only as an evidence/state layer?

## Example

- `assets/example-process-as-is.html` — AS-IS quote-response process with performer lanes, evidence strip, explicit unknown measures, decision/action separation, and distinct response versus escalation outcomes.
