> ⚠️ **SYNTHETIC TEST DATA — not a real SCG document.** Generated for retrieval testing.

# Python Coding Standards

**Department:** Engineering

## Style

- Formatter: `ruff format`, line length 100
- Linter: `ruff check` with the E, F, I, UP, B rule sets enabled
- Type hints required on all public functions; `mypy --strict` on new modules

## Project layout

Use `src/` layout with `pyproject.toml`. Dependencies pinned via `uv.lock`;
never commit a bare `requirements.txt` for a new service.

## Error handling

- Never use a bare `except:` — catch specific exception types
- Do not swallow exceptions silently; log with context or re-raise
- Use `contextlib.suppress` only where the ignored case is genuinely expected

## Testing

`pytest`, minimum 70% line coverage on new code. Fixtures over setUp methods.
Mark slow integration tests with `@pytest.mark.slow`.

## Logging

Structured logging via `structlog`. Never log credentials, API keys, or
customer PII.
