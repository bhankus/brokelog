import io

import pandas as pd
import pytest
from fastapi import HTTPException

from brokelog.parsers import SUPPORTED_BANKS, get_parser
from brokelog.parsers.amex import AmexParser
from brokelog.parsers.barclays import BarclaysParser
from brokelog.parsers.capital_one import CapitalOneParser
from brokelog.parsers.chase import ChaseParser
from brokelog.parsers.usaa import USAAParser
from tests.conftest import (
    AMEX_CSV_CONTENT,
    AMEX_CSV_MISSING_COLUMN,
    BARCLAYS_CSV_CONTENT,
    BARCLAYS_CSV_MISSING_COLUMN,
    CAPITAL_ONE_CSV_CONTENT,
    CAPITAL_ONE_CSV_MISSING_COLUMN,
    CHASE_CSV_CONTENT,
    CHASE_CSV_MISSING_COLUMN,
    USAA_CSV_CONTENT,
    USAA_CSV_MISSING_COLUMN,
)


def _df(csv: str, skiprows: int = 0) -> pd.DataFrame:
    return pd.read_csv(io.StringIO(csv), skiprows=skiprows)


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

    def test_supported_banks_contains_barclays(self):
        assert "barclays" in SUPPORTED_BANKS

    def test_supported_banks_contains_capital_one(self):
        assert "capital_one" in SUPPORTED_BANKS

    def test_supported_banks_contains_usaa(self):
        assert "usaa" in SUPPORTED_BANKS


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


class TestBarclaysParser:
    def test_parse_basic(self):
        parser = BarclaysParser()
        result = parser.parse(_df(BARCLAYS_CSV_CONTENT, skiprows=4), account="Barclays Visa", owner="alice")
        assert len(result) == 3

    def test_purchase_maps_to_debit(self):
        parser = BarclaysParser()
        result = parser.parse(_df(BARCLAYS_CSV_CONTENT, skiprows=4), account="Barclays Visa", owner="alice")
        assert len([t for t in result if t.type == "debit"]) == 2

    def test_payment_maps_to_credit(self):
        parser = BarclaysParser()
        result = parser.parse(_df(BARCLAYS_CSV_CONTENT, skiprows=4), account="Barclays Visa", owner="alice")
        credits = [t for t in result if t.type == "credit"]
        assert len(credits) == 1
        assert "PAYMENT" in credits[0].description

    def test_amount_signs_match_type(self):
        parser = BarclaysParser()
        result = parser.parse(_df(BARCLAYS_CSV_CONTENT, skiprows=4), account="Barclays Visa", owner="alice")
        for t in result:
            if t.type == "debit":
                assert t.amount < 0
            else:
                assert t.amount > 0

    def test_category_mapped(self):
        parser = BarclaysParser()
        result = parser.parse(_df(BARCLAYS_CSV_CONTENT, skiprows=4), account="Barclays Visa", owner="alice")
        assert result[0].category == "DEBIT"
        assert result[2].category == "CREDIT"

    def test_account_and_owner_injected(self):
        parser = BarclaysParser()
        result = parser.parse(_df(BARCLAYS_CSV_CONTENT, skiprows=4), account="My Barclays", owner="bob")
        assert all(t.account == "My Barclays" for t in result)
        assert all(t.owner == "bob" for t in result)

    def test_missing_required_column_raises(self):
        parser = BarclaysParser()
        with pytest.raises(ValueError, match="missing required columns"):
            parser.parse(_df(BARCLAYS_CSV_MISSING_COLUMN, skiprows=4), account="x", owner="y")

    def test_date_parsed_correctly(self):
        from datetime import date

        parser = BarclaysParser()
        result = parser.parse(_df(BARCLAYS_CSV_CONTENT, skiprows=4), account="x", owner="y")
        assert result[0].transaction_date == date(2026, 3, 11)

    def test_skiprows_attribute(self):
        assert BarclaysParser.skiprows == 4


class TestCapitalOneParser:
    def test_parse_basic(self):
        parser = CapitalOneParser()
        result = parser.parse(_df(CAPITAL_ONE_CSV_CONTENT), account="Capital One", owner="alice")
        assert len(result) == 4

    def test_debit_maps_to_negative(self):
        parser = CapitalOneParser()
        result = parser.parse(_df(CAPITAL_ONE_CSV_CONTENT), account="Capital One", owner="alice")
        debits = [t for t in result if t.type == "debit"]
        assert len(debits) == 3
        assert all(t.amount < 0 for t in debits)

    def test_credit_maps_to_positive(self):
        parser = CapitalOneParser()
        result = parser.parse(_df(CAPITAL_ONE_CSV_CONTENT), account="Capital One", owner="alice")
        credits = [t for t in result if t.type == "credit"]
        assert len(credits) == 1
        assert credits[0].amount > 0

    def test_amount_signs_match_type(self):
        parser = CapitalOneParser()
        result = parser.parse(_df(CAPITAL_ONE_CSV_CONTENT), account="Capital One", owner="alice")
        for t in result:
            if t.type == "debit":
                assert t.amount < 0
            else:
                assert t.amount > 0

    def test_category_is_na(self):
        parser = CapitalOneParser()
        result = parser.parse(_df(CAPITAL_ONE_CSV_CONTENT), account="Capital One", owner="alice")
        assert all(t.category == "N/A" for t in result)

    def test_account_and_owner_injected(self):
        parser = CapitalOneParser()
        result = parser.parse(_df(CAPITAL_ONE_CSV_CONTENT), account="My CapOne", owner="bob")
        assert all(t.account == "My CapOne" for t in result)
        assert all(t.owner == "bob" for t in result)

    def test_missing_required_column_raises(self):
        parser = CapitalOneParser()
        with pytest.raises(ValueError, match="missing required columns"):
            parser.parse(_df(CAPITAL_ONE_CSV_MISSING_COLUMN), account="x", owner="y")

    def test_date_parsed_correctly(self):
        from datetime import date

        parser = CapitalOneParser()
        result = parser.parse(_df(CAPITAL_ONE_CSV_CONTENT), account="x", owner="y")
        assert result[0].transaction_date == date(2026, 3, 17)

    def test_skiprows_attribute(self):
        assert CapitalOneParser.skiprows == 0


class TestUSAAParser:
    def test_parse_basic(self):
        parser = USAAParser()
        result = parser.parse(_df(USAA_CSV_CONTENT), account="USAA Checking", owner="alice")
        assert len(result) == 3

    def test_debit_maps_to_negative(self):
        parser = USAAParser()
        result = parser.parse(_df(USAA_CSV_CONTENT), account="USAA Checking", owner="alice")
        debits = [t for t in result if t.type == "debit"]
        assert len(debits) == 1
        assert debits[0].amount < 0

    def test_credits_map_to_positive(self):
        parser = USAAParser()
        result = parser.parse(_df(USAA_CSV_CONTENT), account="USAA Checking", owner="alice")
        credits = [t for t in result if t.type == "credit"]
        assert len(credits) == 2
        assert all(t.amount > 0 for t in credits)

    def test_amount_signs_match_type(self):
        parser = USAAParser()
        result = parser.parse(_df(USAA_CSV_CONTENT), account="USAA Checking", owner="alice")
        for t in result:
            if t.type == "debit":
                assert t.amount < 0
            else:
                assert t.amount > 0

    def test_description_concatenated(self):
        parser = USAAParser()
        result = parser.parse(_df(USAA_CSV_CONTENT), account="USAA Checking", owner="alice")
        assert result[0].description == "ATM Withdrawal Name of bank"

    def test_category_mapped(self):
        parser = USAAParser()
        result = parser.parse(_df(USAA_CSV_CONTENT), account="USAA Checking", owner="alice")
        assert result[0].category == "Cash"
        assert result[2].category == "Interest Income"

    def test_account_and_owner_injected(self):
        parser = USAAParser()
        result = parser.parse(_df(USAA_CSV_CONTENT), account="My USAA", owner="bob")
        assert all(t.account == "My USAA" for t in result)
        assert all(t.owner == "bob" for t in result)

    def test_missing_required_column_raises(self):
        parser = USAAParser()
        with pytest.raises(ValueError, match="missing required columns"):
            parser.parse(_df(USAA_CSV_MISSING_COLUMN), account="x", owner="y")

    def test_date_parsed_correctly(self):
        from datetime import date

        parser = USAAParser()
        result = parser.parse(_df(USAA_CSV_CONTENT), account="x", owner="y")
        assert result[0].transaction_date == date(2026, 3, 20)

    def test_skiprows_attribute(self):
        assert USAAParser.skiprows == 0
