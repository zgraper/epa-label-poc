# 🌿 EPA Pesticide Label POC

A small Python [Streamlit](https://streamlit.io/) proof-of-concept app that
looks up pesticide labels from the
[EPA Pesticide Product Label System (PPLS)](https://ordspub.epa.gov/ords/pesticides/f?p=PPLS:1)
REST API.

---

## Features

- **Free-text query input** — enter a product name, EPA registration number, or a description of what you need.
- **Rule-based intent detection** — filters out non-pesticide queries before hitting the API.
- **EPA PPLS API lookup cascade** — tries registration-number lookup first, then exact product-name match, then partial name (`$like`) wildcard search.
- **Fuzzy-ranked candidate list** — up to 10 results ranked by string similarity using [rapidfuzz](https://github.com/rapidfuzz/RapidFuzz).
- **Product detail display** — shows product name, EPA reg. no., status, signal word, company, active ingredients, use sites, and target pests.
- **In-page PDF viewer** — embeds any label PDFs returned by the API in an iframe; also provides a direct link to open in a new tab.
- **Label-currency warning** — prominent banner reminding users to verify they have the most recent stamped label.

---

## Requirements

- Python 3.10+
- [Streamlit](https://streamlit.io/) ≥ 1.35.0
- [Requests](https://docs.python-requests.org/) ≥ 2.31.0
- [rapidfuzz](https://github.com/rapidfuzz/RapidFuzz) ≥ 3.9.0

All Python dependencies are listed in `requirements.txt`.

---

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/zgraper/epa-label-poc.git
   cd epa-label-poc
   ```

2. **Create and activate a virtual environment** (recommended)

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # macOS / Linux
   .venv\Scripts\activate      # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

---

## Running the App

```bash
streamlit run app.py
```

Streamlit will start a local development server and open the app in your
default browser (typically at `http://localhost:8501`).

---

## Usage

1. Type a product name, EPA registration number (e.g. `524-343`), or a
   description of what you need in the search box.
2. The app detects whether your query is pesticide-label related; if not, it
   prompts you to refine it.
3. Matching products are fetched from the EPA PPLS API and displayed as a
   ranked list. Select one to view its details.
4. Use the PDF viewer to read the label document directly in the page, or open
   it in a new browser tab.

> **⚠️ Important:** Always confirm you are viewing the most recent stamped EPA
> label. A product may have multiple PDFs (supplemental labels, amendments,
> state registrations). Review **all** relevant documents to understand the
> full current terms of registration.

---

## Project Structure

```
epa-label-poc/
├── app.py           # Streamlit UI entry point
├── classifier.py    # Rule-based intent detection & EPA reg-no extraction
├── epa_client.py    # Thin wrapper around the EPA PPLS REST API
├── utils.py         # Fuzzy ranking and field-extraction helpers
└── requirements.txt # Python dependencies
```

### Module Overview

| Module | Responsibility |
|---|---|
| `app.py` | Streamlit page config, layout, query flow, and PDF embed |
| `classifier.py` | `is_pesticide_label_query()` keyword/regex heuristic; `extract_epa_reg_no()` regex |
| `epa_client.py` | `lookup_by_reg_no()`, `lookup_by_product_name_exact()`, `lookup_by_product_name_partial()` |
| `utils.py` | `rank_candidates()`, `extract_active_ingredients()`, `extract_sites()`, `extract_pests()`, `extract_pdf_filenames()`, `epa_pdf_url()` |

---

## Data Source

All product data is retrieved in real time from the publicly available
**EPA Pesticide Product Label System (PPLS)** REST API:

```
https://ordspub.epa.gov/ords/pesticides/ppls/
```

No data is stored locally by this application.

---

## Disclaimer

This tool is a proof-of-concept only. It is not an official EPA product and
makes no guarantees about the completeness, accuracy, or currency of the label
information displayed. Always consult the
[official EPA PPLS website](https://ordspub.epa.gov/ords/pesticides/f?p=PPLS:1)
and verify label documents with the registrant before use.
