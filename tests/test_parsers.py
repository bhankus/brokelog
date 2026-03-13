import io

import pandas as pd
import pytest
from fastapi import HTTPException

from brokelog.parsers import SUPPORTED_BANKS, get_parser
from brokelog.parsers.amex import AmexParser
from brokelog.parsers.chase import ChaseParser
from tests.conftest import AMEX_CSV_CONTENT, AMEX_CSV_MISSING_COLUMN, CHASE_CSV_CONTENT, CHASE_CSV_MISSING_COLUMN


def _df(csv: str) -> pd.DataFrame:
    return pd.read_csv(io.StringIO(csv))


class TestChaseParser:
    def test_parse_basic(self):
        parser = ChaseParser()
        result = parser.parse(_df(CHASE_CSV_CONTENT), account="Chase Checking", owner="alice")
        assert len(result) == 3

    def test_sale_maps_to_debit(self):
        parser = ChaseParser()
        result = parser.parse(_df(CHASE_CSV_CONTENT), account="Chase Checking", owner="alice")
        debits = [t for t in result if t.type == "debit"]
        assert len(debits) == 2

    def test_payment_maps_to_credit(self):
        parser = ChaseParser()
        result = parser.parse(_df(CHASE_CSV_CONTENT), account="Chase Checking", owner="alice")
        credits = [t for t in result if t.type == "credit"]
        assert len(credits) == 1
        assert credits[0].description == "PAYROLL"

    def test_amount_signs_match_type(self):
        parser = ChaseParser()
        result = parser.parse(_df(CHASE_CSV_CONTENT), account="Chase Checking", owner="alice")
        for t in result:
            if t.type == "debit":
                assert t.amount < 0
            else:
                assert t.amount > 0

    def test_blank_category_becomes_na(self):
        parser = ChaseParser()
        result = parser.parse(_df(CHASE_CSV_CONTENT), account="Chase Checking", owner="alice")
        # Second row has no category
        assert result[1].category == "N/A"

    def test_account_and_owner_injected(self):
        parser = ChaseParser()
        result = parser.parse(_df(CHASE_CSV_CONTENT), account="My Account", owner="bob")
        assert all(t.account == "My Account" for t in result)
        assert all(t.owner == "bob" for t in result)

    def test_missing_required_column_raises(self):
        parser = ChaseParser()
        with pytest.raises(ValueError, match="missing required columns"):
            parser.parse(_df(CHASE_CSV_MISSING_COLUMN), account="x", owner="y")

    def test_date_parsed_correctly(self):
        from datetime import date

        parser = ChaseParser()
        result = parser.parse(_df(CHASE_CSV_CONTENT), account="x", owner="y")
        assert result[0].transaction_date == date(2024, 1, 15)


class TestParserRegistry:
    def test_get_parser_known(self):
        parser = get_parser("chase")
        assert isinstance(parser, ChaseParser)

    def test_get_parser_case_insensitive(self):
        parser = get_parser("CHASE")
        assert isinstance(parser, ChaseParser)

    def test_get_parser_unknown_raises_http_400(self):
        with pytest.raises(HTTPException) as exc_info:
            get_parser("unknown_bank")
        assert exc_info.value.status_code == 400

    def test_supported_banks_contains_chase(self):
        assert "chase" in SUPPORTED_BANKS

    def test_supported_banks_contains_amex(self):
        assert "amex" in SUPPORTED_BANKS


class TestAmexParser:
    def test_parse_basic(self):
        parser = AmexParser()
        result = parser.parse(_df(AMEX_CSV_CONTENT), account="Amex Gold", owner="alice")
        assert len(result) == 3

    def test_purchase_maps_to_debit(self):
        parser = AmexParser()
        result = parser.parse(_df(AMEX_CSV_CONTENT), account="Amex Gold", owner="alice")
        assert len([t for t in result if t.type == "debit"]) == 2

    def test_payment_maps_to_credit(self):
        parser = AmexParser()
        result = parser.parse(_df(AMEX_CSV_CONTENT), account="Amex Gold", owner="alice")
        credits = [t for t in result if t.type == "credit"]
        assert len(credits) == 1
        assert credits[0].description == "PAYMENT - THANK YOU"

    def test_amount_signs_match_type(self):
        parser = AmexParser()
        result = parser.parse(_df(AMEX_CSV_CONTENT), account="Amex Gold", owner="alice")
        for t in result:
            if t.type == "debit":
                assert t.amount < 0
            else:
                assert t.amount > 0

    def test_category_mapped(self):
        parser = AmexParser()
        result = parser.parse(_df(AMEX_CSV_CONTENT), account="Amex Gold", owner="alice")
        assert result[0].category == "Shopping"
        assert result[1].category == "Groceries"

    def test_account_and_owner_injected(self):
        parser = AmexParser()
        result = parser.parse(_df(AMEX_CSV_CONTENT), account="My Amex", owner="bob")
        assert all(t.account == "My Amex" for t in result)
        assert all(t.owner == "bob" for t in result)

    def test_missing_required_column_raises(self):
        parser = AmexParser()
        with pytest.raises(ValueError, match="missing required columns"):
            parser.parse(_df(AMEX_CSV_MISSING_COLUMN), account="x", owner="y")

    def test_date_parsed_correctly(self):
        from datetime import date

        parser = AmexParser()
        result = parser.parse(_df(AMEX_CSV_CONTENT), account="x", owner="y")
        assert result[0].transaction_date == date(2024, 1, 15)
