import pandas as pd

from brokelog.models import TransactionCreate
from brokelog.parsers.base import BaseParser

REQUIRED_COLUMNS = {"Transaction Date", "Description", "Type", "Amount"}

TYPE_MAP = {
    "sale": "debit",
    "return": "credit",
    "payment": "credit",
}


class ChaseParser(BaseParser):
    def parse(self, df: pd.DataFrame, account: str, owner: str) -> list[TransactionCreate]:
        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(f"Chase CSV is missing required columns: {missing}")

        transactions: list[TransactionCreate] = []
        for _, row in df.iterrows():
            raw_type = str(row["Type"]).strip().lower()
            txn_type = TYPE_MAP.get(raw_type, "debit")

            category = self._safe_str(row.get("Category"))

            transactions.append(
                TransactionCreate(
                    transaction_date=self._safe_date(row["Transaction Date"], fmt="%m/%d/%Y"),
                    amount=self._safe_float(row["Amount"]),
                    description=self._normalize_description(row["Description"]),
                    category=category,
                    type=txn_type,
                    account=account,
                    owner=owner,
                )
            )

        return transactions
