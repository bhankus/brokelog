import pandas as pd

from brokelog.models import TransactionCreate
from brokelog.parsers.base import BaseParser

REQUIRED_COLUMNS = {
    "Transaction Description",
    "Transaction Date",
    "Transaction Type",
    "Transaction Amount",
}


class CapitalOneParser(BaseParser):

    def parse(self, df: pd.DataFrame, account: str, owner: str) -> list[TransactionCreate]:
        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(f"Capital One CSV is missing required columns: {missing}")

        transactions: list[TransactionCreate] = []
        for _, row in df.iterrows():
            txn_type = self._safe_str(row["Transaction Type"]).lower()  # "debit" or "credit"
            amount = self._safe_float(row["Transaction Amount"])
            # Capital One encodes all amounts as positive; negate debits to match system convention
            if txn_type == "debit":
                amount = -abs(amount)

            transactions.append(
                TransactionCreate(
                    transaction_date=self._safe_date(row["Transaction Date"], fmt="%m/%d/%y"),
                    amount=amount,
                    description=self._normalize_description(row["Transaction Description"]),
                    category="N/A",
                    type=txn_type,
                    account=account,
                    owner=owner,
                )
            )

        return transactions
