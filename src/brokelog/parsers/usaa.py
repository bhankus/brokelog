import pandas as pd

from brokelog.models import TransactionCreate
from brokelog.parsers.base import BaseParser

REQUIRED_COLUMNS = {"Date", "Description", "Original Description", "Category", "Amount"}


class USAAParser(BaseParser):

    def parse(self, df: pd.DataFrame, account: str, owner: str) -> list[TransactionCreate]:
        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(f"USAA CSV is missing required columns: {missing}")

        transactions: list[TransactionCreate] = []
        for _, row in df.iterrows():
            amount = self._safe_float(row["Amount"])
            # USAA amounts are already system-signed: negative=debit, positive=credit
            txn_type = "debit" if amount < 0 else "credit"

            # Concatenate Description and Original Description, skipping N/A parts
            parts = [
                p for p in [
                    self._safe_str(row["Description"]),
                    self._safe_str(row["Original Description"]),
                ]
                if p != "N/A"
            ]
            description = " ".join(parts) if parts else "N/A"

            transactions.append(
                TransactionCreate(
                    transaction_date=self._safe_date(row["Date"], fmt="%Y-%m-%d"),
                    amount=amount,
                    description=description,
                    category=self._safe_str(row["Category"]),
                    type=txn_type,
                    account=account,
                    owner=owner,
                )
            )

        return transactions
