"""
epa_client.py
-------------
Thin wrapper around the EPA Pesticide Product Label System (PPLS) REST API.

Public endpoints used:
  • Registration-number lookup:
      GET https://ordspub.epa.gov/ords/pesticides/ppls/<reg_no>
  • Product-name search (supports partial match via ORDS query):
      GET https://ordspub.epa.gov/ords/pesticides/ppls/?
              q={"productName":"<name>"}&limit=<n>

All calls include a generous timeout and return an empty result rather than
raising, so the UI can degrade gracefully.

TODO (future): add a local metadata index (SQLite or DuckDB) in front of
these calls to cache results and enable offline / low-latency lookups.
"""

from __future__ import annotations

import logging
import urllib.parse

import requests

logger = logging.getLogger(__name__)

_BASE_URL = "https://ordspub.epa.gov/ords/pesticides/ppls"
_TIMEOUT = 10  # seconds
_DEFAULT_LIMIT = 20  # fetch slightly more than we show to allow re-ranking


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get(url: str, params: dict | None = None) -> dict | list | None:
    """Perform a GET request and return parsed JSON, or None on error."""
    try:
        resp = requests.get(url, params=params, timeout=_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.Timeout:
        logger.warning("EPA API timed out: %s", url)
    except requests.exceptions.HTTPError as exc:
        logger.warning("EPA API HTTP error %s: %s", exc.response.status_code, url)
    except requests.exceptions.RequestException as exc:
        logger.warning("EPA API request failed: %s", exc)
    except ValueError:
        logger.warning("EPA API returned non-JSON response: %s", url)
    return None


_PRODUCT_KEYS = frozenset({"productName", "registrationNumber", "regNo"})


def _items_from_response(data: dict | list | None) -> list[dict]:
    """Normalise the varied ORDS response shapes into a flat list of items."""
    if data is None:
        return []
    # ORDS collection endpoint wraps results in {"items": [...]}
    if isinstance(data, dict):
        if "items" in data:
            return data.get("items", [])
        # ORDS single-record endpoint (e.g. /ppls/<reg_no>) returns a bare
        # product dict with no "items" wrapper.  Only wrap it if it contains
        # at least one recognised product field, to avoid treating error
        # responses as product records.
        if _PRODUCT_KEYS.intersection(data):
            return [data]
        return []
    # Some endpoints return a bare list of records.
    if isinstance(data, list):
        return data
    return []


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def lookup_by_reg_no(reg_no: str) -> list[dict]:
    """Look up a single pesticide product by its EPA registration number.

    Args:
        reg_no: Registration number string, e.g. ``"524-308"``.

    Returns:
        A list containing the matching product dict, or an empty list.
    """
    url = f"{_BASE_URL}/{urllib.parse.quote(reg_no, safe='')}"
    data = _get(url)
    return _items_from_response(data)


def lookup_by_reg_no_search(reg_no: str, limit: int = _DEFAULT_LIMIT) -> list[dict]:
    """Search for products by registration number via the collection endpoint.

    This is a fallback for when the direct single-record lookup returns nothing.
    It uses the ORDS ``q`` filter on the ``registrationNumber`` field.

    Args:
        reg_no: Registration number string, e.g. ``"71995-68"``.
        limit:  Maximum number of results to request from the API.

    Returns:
        List of matching product dicts (may be empty).
    """
    import json

    url = _BASE_URL + "/"
    params = {
        "q": json.dumps({"registrationNumber": reg_no}),
        "limit": limit,
    }
    data = _get(url, params=params)
    return _items_from_response(data)


def lookup_by_product_name_exact(name: str, limit: int = _DEFAULT_LIMIT) -> list[dict]:
    """Search for products whose name exactly matches *name* (case-insensitive).

    The ORDS ``q`` parameter accepts a JSON filter object.

    Args:
        name:  Product name to search for.
        limit: Maximum number of results to request from the API.

    Returns:
        List of matching product dicts (may be empty).

    TODO (future): check local index before hitting the network.
    """
    import json

    url = _BASE_URL + "/"
    params = {
        "q": json.dumps({"productName": name}),
        "limit": limit,
    }
    data = _get(url, params=params)
    return _items_from_response(data)


def lookup_by_product_name_partial(name: str, limit: int = _DEFAULT_LIMIT) -> list[dict]:
    """Search for products whose name contains *name* as a substring.

    Uses the ORDS ``%`` wildcard in the filter value.

    Args:
        name:  Partial product name string.
        limit: Maximum number of results to request from the API.

    Returns:
        List of matching product dicts (may be empty).

    TODO (future): check local index before hitting the network.
    """
    import json

    url = _BASE_URL + "/"
    # ORDS supports SQL-style LIKE wildcards inside the q filter value.
    params = {
        "q": json.dumps({"productName": {"$like": f"%{name}%"}}),
        "limit": limit,
    }
    data = _get(url, params=params)
    return _items_from_response(data)
