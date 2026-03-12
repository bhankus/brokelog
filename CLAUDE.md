# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies (including dev)
uv sync

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_parsers.py

# Run a single test by name
uv run pytest tests/test_parsers.py::TestChaseParser::test_sale_maps_to_debit

# Start the dev server
uv run uvicorn brokelog.main:app --reload

# Lint
uv run ruff check src/

# Type check
uv run mypy src/
```

## Architecture

The app is a FastAPI REST API that ingests bank CSV exports, normalizes them through a pluggable parser system, and persists them to SQLite via SQLAlchemy.

**Dual-mode POST endpoint**: `POST /api/v1/transactions` handles two content types in a single route by inspecting the `Content-Type` header:
- `multipart/form-data` → CSV bulk upload → returns `UploadResult`
- `application/json` → single transaction → returns `TransactionRead`

**Parser system**: Adding a new bank requires two steps:
1. Create `src/brokelog/parsers/<bank>.py` extending `BaseParser` (which provides `_safe_str`, `_safe_float`, `_safe_date`, `_normalize_description` helpers)
2. Register in `src/brokelog/parsers/__init__.py` — `get_parser()` does a case-insensitive dict lookup and raises `HTTPException(400)` for unknown banks

**"N/A" convention**: All `TransactionCreate` fields are required with no defaults. When a parser cannot populate a string field from CSV data, it substitutes `"N/A"` using the `BaseParser` helpers — the responsibility lives in the parser layer, not the Pydantic model.

**Amounts are always positive**: `amount` is stored as an absolute value; the `type` field (`"debit"` or `"credit"`) conveys direction. The `@field_validator("amount")` enforces `> 0`.

**Test isolation**: Tests use an in-memory SQLite engine (session-scoped) with a rollback-per-test pattern — each test gets a transaction that rolls back rather than a fresh DB, keeping tests fast. The `client` fixture overrides the `get_db` FastAPI dependency via `app.dependency_overrides`.

**Chase CSV format**: `Transaction Date,Post Date,Description,Category,Type,Amount,Memo` — `Type` values `Sale`→`debit`, `Payment`/`Return`→`credit`. Date format `%m/%d/%Y`. Amounts may be negative in the CSV; `_safe_float` takes the absolute value.
