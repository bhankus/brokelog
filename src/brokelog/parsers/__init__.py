from fastapi import HTTPException

from brokelog.parsers.amex import AmexParser
from brokelog.parsers.barclays import BarclaysParser
from brokelog.parsers.base import BankParser, BaseParser
from brokelog.parsers.capital_one import CapitalOneParser
from brokelog.parsers.chase import ChaseParser

PARSER_REGISTRY: dict[str, type[BaseParser]] = {
    "amex": AmexParser,
    "barclays": BarclaysParser,
    "capital_one": CapitalOneParser,
    "chase": ChaseParser,
}

SUPPORTED_BANKS: list[str] = list(PARSER_REGISTRY.keys())


def get_parser(bank: str) -> BankParser:
    parser_class = PARSER_REGISTRY.get(bank.lower())
    if parser_class is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown bank '{bank}'. Supported banks: {SUPPORTED_BANKS}",
        )
    return parser_class()


__all__ = ["BankParser", "SUPPORTED_BANKS", "get_parser"]
