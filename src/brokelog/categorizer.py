import json
import logging
from pathlib import Path

from rapidfuzz import fuzz, process

logger = logging.getLogger(__name__)

UNCATEGORIZED = "UNCATEGORIZED"
_SCORE_CUTOFF = 80


def load_categories(path: str) -> dict[str, str]:
    """Load a JSON description→category mapping file.

    Returns an empty dict if the file does not exist, allowing the app to
    start without a mapping file (all transactions will be UNCATEGORIZED).
    """
    p = Path(path)
    if not p.exists():
        logger.info(
            "Categories file not found at %s; all transactions will be %s",
            path,
            UNCATEGORIZED,
        )
        return {}
    with p.open() as f:
        data: dict[str, str] = json.load(f)
    return data


def categorize(description: str, mapping: dict[str, str]) -> str:
    """Fuzzy-match a transaction description against the user's mapping.

    Uses rapidfuzz partial_ratio so a key like "Amazon" matches descriptions
    like "AMAZON PRIME 1234" or "Amazon 5436" as long as the score exceeds
    the cutoff (80 by default).

    Returns the matched category string, or "UNCATEGORIZED" if no key scores
    above the cutoff or the mapping is empty.
    """
    if not mapping:
        return UNCATEGORIZED

    # Normalize to lowercase for case-insensitive matching
    lower_desc = description.lower()
    lower_mapping = {k.lower(): v for k, v in mapping.items()}

    result = process.extractOne(
        lower_desc,
        lower_mapping.keys(),
        scorer=fuzz.partial_ratio,
        score_cutoff=_SCORE_CUTOFF,
    )
    if result is None:
        return UNCATEGORIZED
    return lower_mapping[result[0]]
