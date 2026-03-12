from datetime import date
from typing import Any, Protocol

import pandas as pd

from brokelog.models import TransactionCreate


class BankParser(Protocol):
    def parse(self, df: pd.DataFrame, account: str, owner: str) -> list[TransactionCreate]:
        ...


class BaseParser:
    def _safe_float(self, val: Any) -> float:
        if pd.isna(val):
            raise ValueError(f"Cannot convert null/NaN to float: {val!r}")
        # Replace unicode minus (U+2212) with ASCII minus, strip currency symbols
        cleaned = str(val).replace("\u2212", "-").replace("$", "").replace(",", "").strip()
        return abs(float(cleaned))

    def _safe_date(self, val: Any, fmt: str | None = None) -> date:
        if pd.isna(val):
            raise ValueError(f"Cannot convert null/NaN to date: {val!r}")
        parsed = pd.to_datetime(str(val), format=fmt)
        return parsed.date()

    def _normalize_description(self, val: Any) -> str:
        if pd.isna(val):
            return "N/A"
        cleaned = " ".join(str(val).split())
        return cleaned if cleaned else "N/A"

    def _safe_str(self, val: Any) -> str:
        if pd.isna(val):
            return "N/A"
        cleaned = str(val).strip()
        return cleaned if cleaned else "N/A"
