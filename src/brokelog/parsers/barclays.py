import pandas as pd

from brokelog.models import TransactionCreate
from brokelog.parsers.base import BaseParser

REQUIRED_COLUMNS = {"Transaction Date", "Description", "Category", "Amount"}


class BarclaysParser(BaseParser):
    skiprows: int = 4

    def parse(self, df: pd.DataFrame, account: str, owner: str) -> list[TransactionCreate]:
        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(f"Barclays CSV is missing required columns: {missing}")

        transactions: list[TransactionCreate] = []
        for _, row in df.iterrows():
            # Barclays amounts are already system-signed: negative=debit, positive=credit
            amount = self._safe_float(row["Amount"])
            txn_type = self._safe_str(row["Category"]).lower()  # "DEBIT" or "CREDIT"

            transactions.append(
                TransactionCreate(
                    transaction_date=self._safe_date(row["Transaction Date"], fmt="%m/%d/%Y"),
                    amount=amount,
                    description=self._normalize_description(row["Description"]),
                    category=self._safe_str(row["Category"]),
                    type=txn_type,
                    account=account,
                    owner=owner,
                )
            )

        return transactions
