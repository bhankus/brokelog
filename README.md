# Brokelog

REST API for ingesting and categorizing CSV banking transaction exports from multiple institutions.
Transactions are normalized into a common schema and persisted to SQLite.

## Features

- Upload CSV exports from supported banks via `POST /api/v1/transactions`
- Create individual transactions via JSON on the same endpoint
- Filter and paginate transaction history
- Pluggable bank parser system — add new banks by implementing one class
- Auto-generated interactive API docs at `/api/v1/docs`

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) — package manager

## Quick Start

```bash
uv sync
uv run uvicorn brokelog.main:app --reload
```

API docs: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)

## Usage

### Upload a bank CSV

```bash
curl -X POST http://localhost:8000/api/v1/transactions/ \
  -F "file=@chase_export.csv" \
  -F "bank=chase" \
  -F "account=Chase Checking 1234" \
  -F "owner=alice"
```

Response:
```json
{"count": 3, "transaction_ids": [1, 2, 3]}
```

### Create a single transaction (JSON)

```bash
curl -X POST http://localhost:8000/api/v1/transactions/ \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_date": "2024-01-15",
    "amount": 45.99,
    "description": "AMAZON.COM",
    "category": "Shopping",
    "type": "debit",
    "account": "Chase Checking 1234",
    "owner": "alice"
  }'
```

### List transactions

```bash
# All transactions
curl http://localhost:8000/api/v1/transactions/

# Filter by owner with pagination
curl "http://localhost:8000/api/v1/transactions?owner=alice&skip=0&limit=50"
```

## Transaction Schema

| Field              | Type   | Description                          |
|--------------------|--------|--------------------------------------|
| `transaction_date` | date   | Date of the transaction              |
| `amount`           | float  | Signed amount — negative for debits, positive for credits |
| `description`      | string | Merchant or description              |
| `category`         | string | Category (e.g. Shopping, Food)       |
| `type`             | string | `debit` or `credit`                  |
| `account`          | string | Account label                        |
| `owner`            | string | Account owner identifier             |

String fields that cannot be determined from CSV data are stored as `"N/A"`.

## Supported Banks

| Bank  | `bank` param | Notes                                               |
|-------|--------------|-----------------------------------------------------|
| Chase            | `chase` | Standard Chase CSV export (Transaction Date column)          |
| American Express | `amex`  | Standard Amex CSV export (charges positive, payments negative) |

## Adding a New Bank Parser

1. Create `src/brokelog/parsers/mybank.py` with a class that extends `BaseParser`:

```python
from brokelog.parsers.base import BaseParser
from brokelog.models import TransactionCreate
import pandas as pd

class MyBankParser(BaseParser):
    def parse(self, df: pd.DataFrame, account: str, owner: str) -> list[TransactionCreate]:
        # Map your bank's columns to TransactionCreate fields
        # Use self._safe_str(), self._safe_float(), self._safe_date() helpers
        ...
```

2. Register it in `src/brokelog/parsers/__init__.py`:

```python
from brokelog.parsers.mybank import MyBankParser

PARSER_REGISTRY = {
    "chase": ChaseParser,
    "mybank": MyBankParser,   # add this line
}
```

## Development

```bash
# Install dependencies (including dev)
uv sync

# Run tests
uv run pytest

# Lint
uv run ruff check src/

# Type check
uv run mypy src/
```

## Project Structure

```
brokelog/
├── pyproject.toml
├── openapi.yaml
├── README.md
├── src/
│   └── brokelog/
│       ├── main.py              # FastAPI app + lifespan
│       ├── database.py          # SQLAlchemy engine + session
│       ├── models.py            # ORM model + Pydantic schemas
│       ├── parsers/
│       │   ├── __init__.py      # Parser registry + get_parser()
│       │   ├── base.py          # BankParser protocol + BaseParser utilities
│       │   └── chase.py         # Chase CSV parser
│       └── routers/
│           └── transactions.py  # All /api/v1/transactions endpoints
└── tests/
    ├── conftest.py              # Fixtures + CSV sample data
    ├── test_parsers.py          # Unit tests for parsers
    └── test_transactions_router.py  # Integration tests
```
