# Development

## Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Run quality checks:

```bash
ruff check .
black --check .
mypy app
pytest
```
