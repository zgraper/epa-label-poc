"""
utils.py
--------
Shared helpers for ranking candidate products and extracting display data
from raw EPA PPLS API responses.
"""

from rapidfuzz import fuzz


# ---------------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------------

def rank_candidates(query: str, candidates: list[dict], top_n: int = 10) -> list[dict]:
    """Return the top-*n* candidates ranked by fuzzy similarity to *query*.

    Scoring is based on the ``productName`` field using rapidfuzz's
    ``token_set_ratio`` which handles word-order differences well.

    Args:
        query:      The original user query string.
        candidates: List of product dicts from the EPA API.
        top_n:      Maximum number of results to return.

    Returns:
        Sorted list (highest score first) of at most *top_n* dicts, each
        augmented with a ``_score`` key (0-100).

    TODO (future): incorporate additional signals (e.g. local usage stats or
    embedding similarity) to improve ranking beyond pure string similarity.
    """
    scored = []
    q_lower = query.lower()
    for product in candidates:
        name = (product.get("productName") or "").lower()
        score = fuzz.token_set_ratio(q_lower, name)
        scored.append({**product, "_score": score})
    scored.sort(key=lambda p: p["_score"], reverse=True)
    return scored[:top_n]


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def extract_active_ingredients(product: dict) -> list[str]:
    """Return a human-readable list of active ingredient names.

    The field may be absent, a plain string, or a list of dicts with a
    ``chemicalName`` key depending on the API version.

    Args:
        product: Raw product dict from the EPA API.

    Returns:
        List of ingredient name strings (may be empty).
    """
    raw = product.get("activeIngredients") or product.get("active_ingredients")
    if not raw:
        return []
    if isinstance(raw, str):
        return [s.strip() for s in raw.split(";") if s.strip()]
    if isinstance(raw, list):
        names = []
        for item in raw:
            if isinstance(item, dict):
                names.append(item.get("chemicalName") or item.get("name") or str(item))
            else:
                names.append(str(item))
        return names
    return [str(raw)]


def extract_sites(product: dict) -> list[str]:
    """Return a list of use-site strings from the product dict.

    Args:
        product: Raw product dict from the EPA API.

    Returns:
        List of site name strings (may be empty).
    """
    raw = product.get("sites") or product.get("pesticideSites") or []
    if isinstance(raw, str):
        return [s.strip() for s in raw.split(";") if s.strip()]
    if isinstance(raw, list):
        result = []
        for item in raw:
            if isinstance(item, dict):
                result.append(item.get("siteName") or item.get("name") or str(item))
            else:
                result.append(str(item))
        return result
    return []


def extract_pests(product: dict) -> list[str]:
    """Return a list of target-pest strings from the product dict.

    Args:
        product: Raw product dict from the EPA API.

    Returns:
        List of pest name strings (may be empty).
    """
    raw = product.get("pests") or product.get("pesticidePests") or []
    if isinstance(raw, str):
        return [s.strip() for s in raw.split(";") if s.strip()]
    if isinstance(raw, list):
        result = []
        for item in raw:
            if isinstance(item, dict):
                result.append(item.get("pestName") or item.get("name") or str(item))
            else:
                result.append(str(item))
        return result
    return []


def extract_pdf_filenames(product: dict) -> list[str]:
    """Return a list of PDF document filenames from the product dict.

    Args:
        product: Raw product dict from the EPA API.

    Returns:
        List of filename strings (may be empty).
    """
    docs = product.get("documents") or product.get("labelDocuments") or []
    if isinstance(docs, list):
        names = []
        for doc in docs:
            if isinstance(doc, dict):
                fn = doc.get("fileName") or doc.get("filename") or doc.get("documentName")
                if fn:
                    names.append(fn)
            elif isinstance(doc, str):
                names.append(doc)
        return names
    return []


def epa_pdf_url(filename: str) -> str:
    """Build the public EPA PPLS URL for a label PDF.

    Args:
        filename: The bare filename returned by the EPA API.

    Returns:
        Full HTTPS URL to the PDF on the EPA server.
    """
    base = "https://ordspub.epa.gov/ords/pesticides/ppls/labels"
    return f"{base}/{filename}"
