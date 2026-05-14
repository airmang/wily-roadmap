# Verification

Run:

```bash
python3 -m compileall -q runners/custom-workflow
python3 runners/custom-workflow/scripts/validate_execution_package.py runners/custom-workflow/skills/plan-goal-runner/templates/execution-package.md
```

Adjust the second command if the template path differs after bundling.
