"""
app.py
------
EPA Pesticide Label POC – Streamlit UI entry point.

Run with:
    streamlit run app.py

This proof-of-concept demonstrates:
  1. Free-text query acceptance.
  2. Rule-based pesticide-label intent detection.
  3. EPA PPLS API lookup (by reg no → exact name → partial name).
  4. Fuzzy-ranked candidate list (up to 10 results).
  5. Product-detail display (name, reg no, status, signal word, company,
     active ingredients, sites, pests).
  6. In-page PDF embed for any label PDFs returned by the API.
  7. Warning banner about label currency.
"""

import streamlit as st

from classifier import extract_epa_reg_no, is_pesticide_label_query
from epa_client import (
    lookup_by_product_name_exact,
    lookup_by_product_name_partial,
    lookup_by_reg_no,
    lookup_by_reg_no_search,
)
from utils import (
    epa_pdf_url,
    extract_active_ingredients,
    extract_pdf_filenames,
    extract_pests,
    extract_sites,
    rank_candidates,
)

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="EPA Pesticide Label Lookup",
    page_icon="🌿",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Warning banner (requirement 8)
# ---------------------------------------------------------------------------

st.warning(
    "⚠️ **Important:** Always confirm you are viewing the most recent stamped "
    "EPA label. A product may have multiple PDFs (supplemental labels, "
    "amendments, state registrations). Review **all** relevant documents to "
    "understand the full current terms of registration.",
    icon="⚠️",
)

# ---------------------------------------------------------------------------
# Title & description
# ---------------------------------------------------------------------------

st.title("🌿 EPA Pesticide Label Lookup")
st.caption(
    "Search for pesticide labels from the "
    "[EPA Pesticide Product Label System (PPLS)]"
    "(https://ordspub.epa.gov/ords/pesticides/f?p=PPLS:1)"
)

# ---------------------------------------------------------------------------
# Query input (requirement 1)
# ---------------------------------------------------------------------------

query = st.text_input(
    "Enter a product name, EPA registration number, or describe what you need:",
    placeholder="e.g. Roundup PowerMAX  |  524-343  |  herbicide for corn",
)

if not query:
    st.stop()

# ---------------------------------------------------------------------------
# Intent detection (requirement 2)
# ---------------------------------------------------------------------------

if not is_pesticide_label_query(query):
    st.info(
        "ℹ️ This query doesn't appear to be a pesticide-label request. "
        "Try including a product name, EPA registration number, or terms "
        "like 'label', 'herbicide', 'pesticide', etc."
    )
    st.stop()

# ---------------------------------------------------------------------------
# EPA API lookup (requirements 3 & 4)
# ---------------------------------------------------------------------------

candidates: list[dict] = []

with st.spinner("Searching EPA PPLS…"):
    reg_no = extract_epa_reg_no(query)

    if reg_no:
        # Path A: registration-number lookup
        st.caption(f"🔍 Looking up EPA registration number **{reg_no}**…")
        candidates = lookup_by_reg_no(reg_no)
        # If the direct reg-number lookup returned nothing, fall back to a
        # collection-endpoint search filtered by registration number.
        if not candidates:
            candidates = lookup_by_reg_no_search(reg_no)
    else:
        # Path B: exact product-name lookup
        candidates = lookup_by_product_name_exact(query)

        # Path C: fall back to partial match if exact returned nothing
        if not candidates:
            candidates = lookup_by_product_name_partial(query)

# ---------------------------------------------------------------------------
# Handle empty results
# ---------------------------------------------------------------------------

if not candidates:
    st.error(
        "No matching products found in the EPA PPLS database. "
        "Try a different spelling, a shorter name, or include the EPA "
        "registration number (e.g. 524-343)."
    )
    st.stop()

# ---------------------------------------------------------------------------
# Rank and display candidates (requirement 5)
# ---------------------------------------------------------------------------

ranked = rank_candidates(query, candidates, top_n=10)

st.subheader(f"Found {len(ranked)} candidate product(s)")

# Build a display label for each candidate.
def _candidate_label(p: dict) -> str:
    name = p.get("productName") or "Unknown product"
    reg = p.get("registrationNumber") or p.get("regNo") or ""
    status = p.get("status") or p.get("productStatus") or ""
    parts = [name]
    if reg:
        parts.append(f"(Reg. {reg})")
    if status:
        parts.append(f"[{status}]")
    return "  ".join(parts)


selected_idx = st.radio(
    "Select a product to view its label details:",
    range(len(ranked)),
    format_func=lambda i: _candidate_label(ranked[i]),
    index=0,
)
selected_product = ranked[selected_idx]

# ---------------------------------------------------------------------------
# Product detail display (requirement 6)
# ---------------------------------------------------------------------------

st.divider()
st.subheader("📋 Product Details")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"**Product Name:** {selected_product.get('productName') or '—'}")
    st.markdown(
        f"**EPA Reg. No.:** "
        f"{selected_product.get('registrationNumber') or selected_product.get('regNo') or '—'}"
    )
    st.markdown(
        f"**Status:** "
        f"{selected_product.get('status') or selected_product.get('productStatus') or '—'}"
    )
    st.markdown(
        f"**Signal Word:** "
        f"{selected_product.get('signalWord') or selected_product.get('signal_word') or '—'}"
    )

with col2:
    company = (
        selected_product.get("companyName")
        or selected_product.get("registrantName")
        or selected_product.get("company_name")
    )
    if company:
        st.markdown(f"**Company:** {company}")

    ingredients = extract_active_ingredients(selected_product)
    if ingredients:
        st.markdown("**Active Ingredients:**")
        for ing in ingredients:
            st.markdown(f"  - {ing}")
    else:
        st.markdown("**Active Ingredients:** —")

sites = extract_sites(selected_product)
pests = extract_pests(selected_product)

if sites:
    with st.expander("🌾 Use Sites", expanded=False):
        for site in sites:
            st.markdown(f"- {site}")

if pests:
    with st.expander("🐛 Target Pests", expanded=False):
        for pest in pests:
            st.markdown(f"- {pest}")

# ---------------------------------------------------------------------------
# PDF selection and embed (requirement 7)
# ---------------------------------------------------------------------------

pdf_filenames = extract_pdf_filenames(selected_product)

if pdf_filenames:
    st.divider()
    st.subheader("📄 Label PDFs")
    st.caption(
        "Multiple PDFs may exist for this product (e.g. the master label, "
        "supplemental labels, and state-specific amendments). "
        "Review all that are relevant to your use."
    )
    chosen_pdf = st.selectbox("Choose a PDF to view:", pdf_filenames)
    pdf_url = epa_pdf_url(chosen_pdf)
    st.markdown(f"[🔗 Open in new tab]({pdf_url})", unsafe_allow_html=False)
    # Embed the PDF via an iframe.
    st.components.v1.iframe(pdf_url, height=800, scrolling=True)
else:
    st.info(
        "No PDF label files were returned by the EPA API for this product. "
        "Visit the "
        "[EPA PPLS website](https://ordspub.epa.gov/ords/pesticides/f?p=PPLS:1) "
        "directly to search for label documents."
    )
