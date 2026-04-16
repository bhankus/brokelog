import json
import tempfile
from pathlib import Path

import pytest

from brokelog.categorizer import UNCATEGORIZED, categorize, load_categories


class TestLoadCategories:
    def test_returns_empty_dict_for_missing_file(self):
        result = load_categories("/nonexistent/path/categories.json")
        assert result == {}

    def test_loads_valid_json_file(self, tmp_path: Path):
        mapping = {"Amazon": "Shopping", "Netflix": "Entertainment"}
        p = tmp_path / "categories.json"
        p.write_text(json.dumps(mapping))
        result = load_categories(str(p))
        assert result == mapping

    def test_returns_all_entries(self, tmp_path: Path):
        mapping = {"Amazon": "Shopping", "Whole Foods": "Groceries", "Netflix": "Entertainment"}
        p = tmp_path / "categories.json"
        p.write_text(json.dumps(mapping))
        result = load_categories(str(p))
        assert len(result) == 3


class TestCategorize:
    MAPPING = {
        "Amazon": "Shopping",
        "Whole Foods": "Groceries",
        "Netflix": "Entertainment",
        "Payroll": "Income",
    }

    def test_exact_match(self):
        assert categorize("Amazon", self.MAPPING) == "Shopping"

    def test_partial_match_with_suffix(self):
        # "Amazon 5436" should match key "Amazon"
        assert categorize("Amazon 5436", self.MAPPING) == "Shopping"

    def test_partial_match_uppercase(self):
        # Case-insensitive: "AMAZON.COM" should still match "Amazon"
        assert categorize("AMAZON.COM", self.MAPPING) == "Shopping"

    def test_partial_match_mixed_case(self):
        assert categorize("NETFLIX SUBSCRIPTION", self.MAPPING) == "Entertainment"

    def test_partial_match_multi_word_key(self):
        assert categorize("WHOLE FOODS MARKET 1234", self.MAPPING) == "Groceries"

    def test_no_match_returns_uncategorized(self):
        assert categorize("SOME UNKNOWN MERCHANT", self.MAPPING) == UNCATEGORIZED

    def test_empty_mapping_returns_uncategorized(self):
        assert categorize("Amazon", {}) == UNCATEGORIZED

    def test_returns_uncategorized_string_literal(self):
        assert categorize("XYZ", {}) == "UNCATEGORIZED"

    def test_payroll_match(self):
        assert categorize("PAYROLL DIRECT DEPOSIT", self.MAPPING) == "Income"

    def test_unrelated_description_does_not_match(self):
        # "Amaz" is too short to trigger a false positive above threshold
        result = categorize("TOTAL RANDOM STORE", self.MAPPING)
        assert result == UNCATEGORIZED
