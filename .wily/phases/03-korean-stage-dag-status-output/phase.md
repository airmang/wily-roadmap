# Phase 03: Korean Stage-Based DAG Status Output

## Purpose

Change `wily-status` from English prose lists to Korean user-facing status output with a compact stage-based DAG summary.

## Expected Starting Conditions

- Phase 02 is done.
- Command skill consistency rules are settled.
- Current `wily-status` output already shows all phases and executable pending phases.

## Likely Files

- `scripts/wily_state_summary.py`
- `tests/test_wily_state_summary.py`
- `skills/wily-status/SKILL.md`
- `skills/wily-workflow/SKILL.md`
- `skills/wily-workflow/references/planning-style.md`

## Completion Criteria

- `wily-status` prints Korean labels for user-facing headings and progress text.
- Phase status labels display in Korean while stored roadmap markers remain English.
- The phase overview uses a stage-based DAG layout, not recursive indentation that drifts right as roadmaps grow.
- Parallel phases with the same dependency level are grouped under the same stage.
- Multi-dependency phases show an explicit `의존:` line instead of forcing an inaccurate tree edge.
- Tests cover Korean labels, the stage layout, parallel grouping, and multi-dependency annotation.

## Known Risks

- The helper script currently has no locale flag. This phase may choose Korean as the Wily default for status output, while keeping machine-facing file markers in English.
- DAG layout should stay deterministic and simple. Do not introduce Graphviz or Mermaid rendering as a dependency in this phase.
