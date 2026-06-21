# Mutual Fund FAQ Assistant (Facts-Only Q&A)

A compliant, facts-only FAQ assistant for mutual fund schemes using Groww as the reference product context. The chatbot answers objective, verifiable queries by retrieving facts exclusively from 5 specified ICICI Prudential direct growth fund URLs, strictly refusing to provide investment advice, forecasts, or comparative recommendations.

---

## Documentation

| Document | Path |
| :--- | :--- |
| **Problem Statement** | [`doc/problemStatement.md`](doc/problemStatement.md) |
| **Architecture Specification** | [`doc/architecture.md`](doc/architecture.md) |

---

## Target Schemes & URLs

The chatbot's corpus is restricted to the following 5 Groww pages:
1. [ICICI Prudential Large Cap Fund Direct Growth](https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth)
2. [ICICI Prudential Silver ETF FoF Direct Growth](https://groww.in/mutual-funds/icici-prudential-silver-etf-fof-direct-growth)
3. [ICICI Prudential Dynamic Plan Direct Growth](https://groww.in/mutual-funds/icici-prudential-dynamic-plan-direct-growth)
4. [ICICI Prudential Infrastructure Fund Direct Growth](https://groww.in/mutual-funds/icici-prudential-infrastructure-fund-direct-growth)
5. [ICICI Prudential Balanced Direct Growth](https://groww.in/mutual-funds/icici-prudential-balanced-direct-growth)

---

## Requirements

- Python 3.11+
- Virtual environment (`.venv`) with installed requirements.

---

## Setup

```bash
cd "Week 8"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and supply a valid Groq API key in LLM_API_KEY
```

---

## Repository Structure

```text
Week 8/
├── doc/
│   ├── problemStatement.md
│   └── architecture.md
├── data/
│   ├── raw/                  # Caches scraped raw html pages
│   └── processed/            # Serialized JSON document database (schemes.json)
├── src/
│   └── app/
│       ├── config.py         # Configuration variables and target urls
│       ├── main.py           # Streamlit UI dashboard
│       ├── models/
│       │   └── domain.py     # Scheme, Chunk, and Response schemas
│       ├── ingestion/
│       │   ├── scraper.py    # BeautifulSoup raw groww crawler
│       │   ├── normalizer.py # JSON-LD parser and semantic chunker
│       │   └── scheduler.py  # Daily ingestion cron job
│       ├── security/
│       │   ├── pii_redactor.py      # PII regex filter
│       │   └── intent_classifier.py # Filters advisory queries
│       └── services/
│           ├── retriever.py    # Structured and text TF-IDF retriever
│           ├── prompt_builder.py # Prompt compiler
│           ├── llm_client.py   # Groq API SDK wrapper
│           └── orchestrator.py # Flow orchestrator and fallback handler
├── tests/                    # Testing suite
├── requirements.txt
└── README.md
```

---

## Execution Commands

### 1. Ingest Data (Crawl & Parse Pages)
To scrape the 5 URLs and generate the local document store:
```bash
PYTHONPATH="." .venv/bin/python src/app/ingestion/normalizer.py
```

### 2. Run Daily Ingestion Scheduler
To trigger the daily ingestion background job:
```bash
PYTHONPATH="." .venv/bin/python src/app/ingestion/scheduler.py
```

### 3. Run Streamlit UI
```bash
PYTHONPATH="." .venv/bin/streamlit run src/app/main.py
```

### 4. Run Tests
```bash
PYTHONPATH="." .venv/bin/pytest tests/
```

---

## Configuration (`.env`)

Ensure the following variables are configured:
- `LLM_PROVIDER`: Set to `groq` (default).
- `LLM_API_KEY`: Generate a key from [console.groq.com](https://console.groq.com/).
- `LLM_MODEL`: Defaults to `llama-3.3-70b-versatile`.
- `LLM_TEMPERATURE`: Keeps creativity low (`0.2`) to prevent hallucinated advice.
- `DATA_STORE_PATH`: Points to `data/processed/schemes.json`.
- `RAW_DATA_PATH`: Points to `data/raw/`.
