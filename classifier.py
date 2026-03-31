"""
classifier.py
-------------
Rule-based classifier that decides whether a free-text query looks like a
pesticide-label request and, if so, whether it contains an EPA registration
number.

No ML model is used here intentionally; the logic is easy to read and to
extend.  A future version could swap in a small intent-classification model
(e.g. a fine-tuned sentence-transformer) without changing the public API.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Keyword heuristics
# ---------------------------------------------------------------------------

# Terms that strongly suggest the user is asking about a pesticide / label.
_PESTICIDE_KEYWORDS = {
    "pesticide",
    "herbicide",
    "insecticide",
    "fungicide",
    "rodenticide",
    "label",
    "epa reg",
    "epa registration",
    "registration number",
    "reg no",
    "active ingredient",
    "signal word",
    "caution",
    "warning",
    "danger",
    "pest",
    "weed",
    "crop",
    "spray",
    "formulation",
    "ppls",
}

# Pattern for a bare EPA registration number: "12345-678" or "12345-678-901".
_REG_NO_PATTERN = re.compile(
    r"\b(\d{1,6}-\d{1,6}(?:-\d{1,6})?)\b"
)


def is_pesticide_label_query(text: str) -> bool:
    """Return True if *text* looks like a pesticide-label lookup request.

    The check is intentionally permissive so that natural-language queries
    such as "show me the label for Roundup" are caught, as well as raw
    registration-number lookups.

    Args:
        text: The raw user query.

    Returns:
        True when the query appears to be pesticide-label related.
    """
    normalised = text.lower()

    # If an EPA reg number is present, treat it as a label request.
    if _REG_NO_PATTERN.search(normalised):
        return True

    # Otherwise check for keyword overlap.
    for keyword in _PESTICIDE_KEYWORDS:
        if " " in keyword:
            # Multi-word keywords: substring match against the full normalised text.
            if keyword in normalised:
                return True
        else:
            # Single-word keywords: exact word match to avoid substring false positives
            # (e.g. 'crop' matching 'acropolis').
            words = set(re.split(r"\W+", normalised))
            if keyword in words:
                return True

    return False


def extract_epa_reg_no(text: str) -> str | None:
    """Extract the first EPA registration number from *text*, if present.

    EPA registration numbers follow the pattern ``XXXXX-XXXXX`` or
    ``XXXXX-XXXXX-XXXXX`` (registrant-product[-supplemental]).

    Args:
        text: The raw user query.

    Returns:
        The matched registration number string, or ``None``.
    """
    match = _REG_NO_PATTERN.search(text)
    return match.group(1) if match else None
