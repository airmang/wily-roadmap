# Plan

1. Add parser regression tests for Wily roadmap YAML subset support:
   - folded block scalar (`>-`) under a phase field;
   - literal block scalar (`|`) under a phase field;
   - block list (`depends_on:\n  - id`) under a phase field.
2. Add lifecycle regression coverage proving `wily start` can rewrite a roadmap containing block scalar/list fields without losing the semantic summary or creating a bogus dependency phase.
3. Extend the local roadmap parser in `scripts/wily_state_summary.py` instead of adding a new runtime dependency:
   - recognize phase starts only at the phase item indentation;
   - parse indented block list items into the current key;
   - parse `|`/`|-` and `>`/`>-` block scalars into strings.
4. Extend `serialize_roadmap` so multi-line strings are emitted as block scalars, while existing scalar and inline-list output stays compatible.
5. Run focused parser/lifecycle tests, py_compile, then the full unittest suite.
