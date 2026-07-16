# Contributing

Thank you for contributing to PDF Tools.

## Development Workflow

1. Create a feature branch from `main`.
2. Keep changes focused on a single logical feature or fix.
3. Run before committing:

```bash
ruff check .
black --check .
mypy app
pytest
```

4. Submit a pull request with a clear description.

## Coding Standards

- Python 3.13+
- Type hints for public interfaces.
- Keep functions small and focused.
- Add or update tests for behavior changes.
- Maintain backward compatibility for published API endpoints where practical.
