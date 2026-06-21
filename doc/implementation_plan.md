# Implementation Plan - HDFC Mutual Fund FAQ Assistant (Facts-Only Q&A)

This plan outlines the phase-wise implementation details for building a facts-only, RAG-based FAQ assistant scoped strictly to five HDFC Mutual Fund scheme pages on Groww. The system uses local vector storage (ChromaDB), local embeddings (sentence-transformers), a stateless FastAPI backend, and strict pre-retrieval intent classification and post-generation compliance checks to ensure facts-only responses.

This plan aligns with the updated [architecture.md](file:///Users/akshatmandavgane/Documents/NextLeap_ProductResources/Week%208/doc/architecture.md) and [problemStatement.md](file:///Users/akshatmandavgane/Documents/NextLeap_ProductResources/Week%208/doc/problemStatement.md).

---

## User Review Required

> [!IMPORTANT]
> **Statelessness and Privacy:** The API is strictly stateless. There are no session store tables, database connections tracking user chats, or analytical logging containing user inputs. Any contextual/history tracking is limited to the client-side browser UI.
> 
> **Offline-First Index Refresh:** Embeddings and database indexing are performed offline via a daily scheduler job. The online QA endpoint reads from the local vector database and metadata index and is never blocked during ingestion.
> 
> **Vector DB Selection (ChromaDB over FAISS):** ChromaDB has been selected as the vector database because it natively supports first-class metadata filtering (essential for filtering searches by `scheme_slug` or `section` before retrieval) and self-contained document text storage. FAISS lacks native metadata filtering and raw text management, which would introduce excessive customization overhead for our small (~83 chunks) corpus.


---

## Open Questions

None. The system parameters (ChromaDB, FastAPI, `bge-small-en-v1.5` embeddings, and Groq client settings) are locked and derived directly from the updated [architecture.md](file:///Users/akshatmandavgane/Documents/NextLeap_ProductResources/Week%208/doc/architecture.md).

---

## Proposed Changes

We will restructure the project from the previous file-based JSON store layout to the modular RAG pipeline structure in 7 sequential implementation phases.

### Phase 1: Configuration & Environment Setup

#### [NEW] [corpus.yaml](file:///Users/akshatmandavgane/Documents/NextLeap_ProductResources/Week%208/config/corpus.yaml)
*   Define metadata configurations for the 5 target HDFC mutual fund URLs.
*   Store target URL mappings, scheme names, slugs, category labels, and categories to assist in scheme resolution.

---

### Phase 2: Ingestion & Parsing (Offline Pipeline)

#### [NEW] [fetch.py](file:///Users/akshatmandavgane/Documents/NextLeap_ProductResources/Week%208/ingestion/fetch.py)
*   Fetch raw HTML from the 5 Groww URLs listed in the corpus configuration.
*   Implement anti-bot headers and connection parameters.
*   Store downloaded pages in `data/raw/` with a timestamp to support offline recovery.

#### [NEW] [parse.py](file:///Users/akshatmandavgane/Documents/NextLeap_ProductResources/Week%208/ingestion/parse.py)
*   Clean raw HTML, strip dynamic scripts, styles, headers, and global navigation footers.
*   Extract core mutual fund text sections and categorize them into semantic tags: `overview`, `expense_ratio`, `exit_load`, `minimum_investment`, `benchmark`, `tax`, `fund_management`, `investment_objective`, and `fund_house`.

---

### Phase 3: Semantic Chunking & Vector DB Indexing

#### [NEW] [chunk.py](file:///Users/akshatmandavgane/Documents/NextLeap_ProductResources/Week%208/ingestion/chunk.py)
*   Implement section-aware chunking strategy:
    *   **Small sections ($\leq$ 200 words):** `expense_ratio`, `exit_load`, `minimum_investment`, `benchmark`, `tax`, `investment_objective` kept as single whole chunks.
    *   **Large sections ($>$ 200 words):**
        *   `fund_management`: Split by individual manager profile blocks (delimited by name/initial patterns).
        *   `overview`, `fund_house`: Recursive character split (~200–300 tokens, 50-token overlap) respecting sentence (`. `) or paragraph (`\n`) boundaries.
    *   **Format:** Prepend contextual schema header to each chunk (`Scheme: <name> | Section: <section> | Content: <text>`).

#### [NEW] [index.py](file:///Users/akshatmandavgane/Documents/NextLeap_ProductResources/Week%208/ingestion/index.py)
*   Initialize local embedding pipeline (e.g. `sentence-transformers` using `BAAI/bge-small-en-v1.5` or equivalent model).
*   Initialize ChromaDB / local Vector DB on disk (`data/index/`).
*   Embed parsed chunks and insert them into the Vector Store with metadata (`source_url`, `scheme_name`, `section`, `last_updated`).
*   Write updated scheme statistics (fetch timestamp, name, slug) to the local JSON metadata file.

#### [NEW] [run.py](file:///Users/akshatmandavgane/Documents/NextLeap_ProductResources/Week%208/ingestion/run.py)
*   Orchestrate the ingestion steps sequentially (`fetch` $\rightarrow$ `parse` $\rightarrow$ `chunk` $\rightarrow$ `index`).
*   Implement atomic indexing so retrieval services can continue reading from the previous database state during rebuilds.

#### [NEW] [daily.py](file:///Users/akshatmandavgane/Documents/NextLeap_ProductResources/Week%208/scheduler/daily.py)
*   Background process scheduler (using `APScheduler` or crontab) to trigger `run.py` once every 24 hours.

---

### Phase 4: Query Classification & Security Guards

#### [NEW] [classifier.py](file:///Users/akshatmandavgane/Documents/NextLeap_ProductResources/Week%208/app/classifier.py)
*   Analyze incoming query and route to either RAG path or Refusal path.
*   Check if query is:
    *   `Factual` $\rightarrow$ Proceed to retrieval (e.g. expense ratios, manager tenure).
    *   `Advisory` / `Comparison` / `Performance` $\rightarrow$ Route to refusal handler.
    *   `Out of Scope` $\rightarrow$ Route to out-of-scope refusal template.
*   Apply high-performance regex scanning to match and redact PII patterns (PAN, Aadhaar, bank accounts, emails, phone numbers).

---

### Phase 5: Two-Stage Context Retrieval

#### [NEW] [retriever.py](file:///Users/akshatmandavgane/Documents/NextLeap_ProductResources/Week%208/app/retriever.py)
*   Implement two-stage context search over database:
    1.  **Scheme Resolution:** Resolve target fund slug from query tokens or name matching.
    2.  **Vector Search:** Query ChromaDB filtering by resolved `source_url` or `scheme_name`. Boost chunks matching metadata `section` flags if keyword categories are identified in the query (e.g., manager names, exit loads).

---

### Phase 6: Constrained Generation & Compliance Validation

#### [NEW] [generator.py](file:///Users/akshatmandavgane/Documents/NextLeap_ProductResources/Week%208/app/generator.py)
*   Assemble prompt with system instructions strictly limiting replies to the retrieved context chunks.
*   Call Groq API SDK (using `llama-3.3-70b-versatile` or `llama3-70b-8192`) with temperature `0.2` and return the response.

#### [NEW] [validator.py](file:///Users/akshatmandavgane/Documents/NextLeap_ProductResources/Week%208/app/validator.py)
*   Audit generated text to assert that:
    1.  Answer contains $\leq$ 3 sentences.
    2.  No advisory or comparative language is present (e.g. "better", "recommend", "advice").
    3.  Fact check: key statistics matched against metadata index parameters.
    4.  Citations matches the source URL in the allowlist database.

#### [NEW] [formatter.py](file:///Users/akshatmandavgane/Documents/NextLeap_ProductResources/Week%208/app/formatter.py)
*   Formulate standard output JSON response with the final text answer, citation URL link, and the static `Last updated from sources: <date>` footer.

---

### Phase 7: FastAPI Endpoint & Web UI Integration

#### [NEW] [main.py](file:///Users/akshatmandavgane/Documents/NextLeap_ProductResources/Week%208/app/main.py)
*   Expose FastAPI application router and define standard endpoint `POST /api/chat` accepting `{ "message": string }`.
*   Handle liveness checks via `GET /health` to ensure ChromaDB database is loaded.

#### [NEW] [index.html](file:///Users/akshatmandavgane/Documents/NextLeap_ProductResources/Week%208/ui/index.html)
*   Create a minimal, high-aesthetic HTML and JS single-page chat dashboard.
*   Incorporate Groww styling aesthetics, render markdown responses, display example cards, and output the required warning disclaimer.

---

### Clean Up / Archive Old Structural Layout

#### [DELETE] [config.py](file:///Users/akshatmandavgane/Documents/NextLeap_ProductResources/Week%208/src/app/config.py)
#### [DELETE] [main.py](file:///Users/akshatmandavgane/Documents/NextLeap_ProductResources/Week%208/src/app/main.py)
#### [DELETE] [domain.py](file:///Users/akshatmandavgane/Documents/NextLeap_ProductResources/Week%208/src/app/models/domain.py)
#### [DELETE] [scraper.py](file:///Users/akshatmandavgane/Documents/NextLeap_ProductResources/Week%208/src/app/ingestion/scraper.py)
#### [DELETE] [normalizer.py](file:///Users/akshatmandavgane/Documents/NextLeap_ProductResources/Week%208/src/app/ingestion/normalizer.py)
#### [DELETE] [scheduler.py](file:///Users/akshatmandavgane/Documents/NextLeap_ProductResources/Week%208/src/app/ingestion/scheduler.py)
#### [DELETE] [pii_redactor.py](file:///Users/akshatmandavgane/Documents/NextLeap_ProductResources/Week%208/src/app/security/pii_redactor.py)
#### [DELETE] [intent_classifier.py](file:///Users/akshatmandavgane/Documents/NextLeap_ProductResources/Week%208/src/app/security/intent_classifier.py)
#### [DELETE] [retriever.py](file:///Users/akshatmandavgane/Documents/NextLeap_ProductResources/Week%208/src/app/services/retriever.py)
#### [DELETE] [prompt_builder.py](file:///Users/akshatmandavgane/Documents/NextLeap_ProductResources/Week%208/src/app/services/prompt_builder.py)
#### [DELETE] [llm_client.py](file:///Users/akshatmandavgane/Documents/NextLeap_ProductResources/Week%208/src/app/services/llm_client.py)
#### [DELETE] [orchestrator.py](file:///Users/akshatmandavgane/Documents/NextLeap_ProductResources/Week%208/src/app/services/orchestrator.py)

---

## Verification Plan

### Automated Tests
Execute unit and integration test assertions covering classification logic, database retrievals, and compliance blocks:
```bash
PYTHONPATH="." .venv/bin/pytest tests/test_classifier.py
PYTHONPATH="." .venv/bin/pytest tests/test_retrieval.py
PYTHONPATH="." .venv/bin/pytest tests/test_refusal.py
```

### Manual Verification
1. Run ingestion pipeline CLI entrypoint:
   ```bash
   PYTHONPATH="." .venv/bin/python ingestion/run.py
   ```
2. Start the FastAPI backend:
   ```bash
   PYTHONPATH="." .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
3. Test API endpoint with curl:
   ```bash
   curl -X POST http://127.0.0.1:8000/api/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "Who is the fund manager of HDFC Mid Cap?"}'
   ```
4. Query with advisory prompts (e.g. "Should I invest in gold?") to ensure the classifier blocks retrieval and routes to educational SEBI/AMFI links.
5. Verify PII triggers block queries immediately.
6. Open the HTML interface `ui/index.html` in browser to test the full end-to-end chat flow.
