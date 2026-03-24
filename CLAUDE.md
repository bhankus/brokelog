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

**Amount sign convention**: `amount` preserves the sign from the source CSV — negative for outflows (debits/purchases), positive for inflows (credits/payments). The `type` field (`"debit"` or `"credit"`) is set independently from the CSV's transaction type column. The `@field_validator("amount")` rejects zero but allows negative values.

**Test isolation**: Tests use an in-memory SQLite engine (session-scoped) with a rollback-per-test pattern — each test gets a transaction that rolls back rather than a fresh DB, keeping tests fast. The `client` fixture overrides the `get_db` FastAPI dependency via `app.dependency_overrides`.

**Chase CSV format**: `Transaction Date,Post Date,Description,Category,Type,Amount,Memo` — `Type` values `Sale`→`debit`, `Payment`/`Return`→`credit`. Date format `%m/%d/%Y`. Amounts in the CSV are negative for purchases and positive for payments; `_safe_float` preserves the sign.

**Amex CSV format**: `Date,Description,Amount,Extended Details,Appears On Your Statement As,Address,City/State,Zip Code,Country,Reference,Category` — no explicit type column; type is inferred from sign after negation. Date format `%m/%d/%y` (2-digit year, e.g. `11/9/24`). Amex encodes purchases as positive and payments as negative; the parser negates amounts to match the system convention (negative = debit, positive = credit).

**Barclays CSV format**: First 4 lines are metadata (bank name, account number, balance, blank line); headers are on line 5: `Transaction Date,Description,Category,Amount`. The `Category` column contains `"DEBIT"` or `"CREDIT"` and maps directly to the `type` field (lowercased). Amounts are already system-signed (negative = debit, positive = credit). Date format `%m/%d/%Y`. The `skiprows = 4` class attribute on `BarclaysParser` tells the upload router to skip the metadata lines when reading the CSV.

**Capital One CSV format**: Headers on line 1: `Account Number,Transaction Description,Transaction Date,Transaction Type,Transaction Amount,Balance`. `Account Number` and `Balance` columns are ignored. All amounts in the CSV are positive; the parser negates `Transaction Amount` for `"Debit"` transactions to match system convention (negative = debit, positive = credit). Type is lowercased directly from `Transaction Type`. No category column — `"N/A"` is used. Date format `%m/%d/%y` (2-digit year). No `skiprows` needed.
