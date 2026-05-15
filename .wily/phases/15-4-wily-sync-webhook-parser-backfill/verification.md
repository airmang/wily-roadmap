# Verification

Expected checks:

```bash
python3 -m pytest tests/test_parser.py tests/test_webhook_signature.py
python3 -m py_compile app/sync/webhook.py app/sync/pull.py app/sync/parser.py
```

Add an integration fixture using this repository's `.wily/roadmap.yaml` and one `stage.yaml`.

