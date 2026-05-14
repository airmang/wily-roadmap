# Planner

Use `superpowers:writing-plans` before implementation.

The plan should be test-driven and should keep the implementation local-first:

- model update states before changing code
- test zip/non-git detection first
- test dirty git refusal
- test already-current local repository behavior with a local bare remote
- add command skill and manifest exposure after CLI behavior is stable
