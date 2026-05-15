# Verification

Expected checks:

```bash
python3 -m pytest tests/test_pr_writer.py tests/test_toggle_status.py
python3 -m py_compile app/actions/pr_writer.py app/actions/toggle_status.py
```

Mock GitHub API calls unless explicit credentials and repository approval are provided.

