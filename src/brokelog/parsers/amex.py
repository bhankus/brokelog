import pandas as pd

from brokelog.models import TransactionCreate
from brokelog.parsers.base import BaseParser

REQUIRED_COLUMNS = {"Date", "Description", "Amount"}


class AmexParser(BaseParser):
    def parse(self, df: pd.DataFrame, account: str, owner: str) -> list[TransactionCreate]:
        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(f"Amex CSV is missing required columns: {missing}")

        transactions: list[TransactionCreate] = []
        for _, row in df.iterrows():
            # Negate: Amex positive = purchase (outflow), negative = payment (inflow)
            # After negation: negative = debit, positive = credit
            amount = -self._safe_float(row["Amount"])
            txn_type = "debit" if amount < 0 else "credit"

            transactions.append(
                TransactionCreate(
                    transaction_date=self._safe_date(row["Date"], fmt="%m/%d/%y"),
                    amount=amount,
                    description=self._normalize_description(row["Description"]),
                    category=self._safe_str(row.get("Category")),
                    type=txn_type,
                    account=account,
                    owner=owner,
                )
            )

        return transactions
