# Planner

Recommended planner: superpowers:test-driven-development

Use `superpowers:systematic-debugging` to confirm the parser data flow, then use TDD:

- Add parser tests for folded and literal block scalars.
- Add parser tests for nested block lists under a phase field.
- Add lifecycle command regression coverage showing `start` does not create bogus phases or lose summary text.
- Implement the smallest roadmap YAML subset support needed for those tests.
