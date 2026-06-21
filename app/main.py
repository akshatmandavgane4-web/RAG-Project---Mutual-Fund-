import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Dict, Any

from app.classifier import QueryClassifier
from app.retriever import RAGRetriever
from app.generator import RAGGenerator
from app.validator import ResponseValidator
from app.formatter import ResponseFormatter

app = FastAPI(
    title="HDFC Mutual Fund FAQ Assistant",
    description="A facts-only retrieval and compliance Q&A service scoped to target HDFC mutual fund schemes.",
    version="1.0.0"
)

# Enable CORS for standard web client connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
classifier = QueryClassifier()
retriever = RAGRetriever()
generator = RAGGenerator()
validator = ResponseValidator()
formatter = ResponseFormatter()

class QueryRequest(BaseModel):
    message: str

class QueryResponse(BaseModel):
    answer: str
    citation_url: str
    last_updated: str
    is_refusal: bool
    disclaimer: str

@app.get("/health")
async def health():
    try:
        # Check ChromaDB connectivity
        retriever.client.heartbeat()
        db_loaded = True
    except Exception as e:
        print(f"Health check database error: {e}")
        db_loaded = False
        
    return {
        "status": "healthy" if db_loaded else "unhealthy",
        "database_loaded": db_loaded
    }

@app.post("/api/chat", response_model=QueryResponse)
async def chat(request: QueryRequest):
    query = request.message
    
    # 1. PII Scan
    is_pii, redacted_query = classifier.scan_for_pii(query)
    if is_pii:
        res = classifier.handle_refusal("factual", pii_detected=True)
        return QueryResponse(
            answer=res["answer"],
            citation_url=res["citation_url"],
            last_updated=res["last_updated"],
            is_refusal=res["is_refusal"],
            disclaimer="Facts-only. No investment advice."
        )

    # 2. Intent Classification
    intent = classifier.classify_intent(redacted_query)
    if intent != "factual":
        res = classifier.handle_refusal(intent)
        return QueryResponse(
            answer=res["answer"],
            citation_url=res["citation_url"],
            last_updated=res["last_updated"],
            is_refusal=res["is_refusal"],
            disclaimer="Facts-only. No investment advice."
        )

    # 3. Retrieve Context
    retrieval_res = retriever.retrieve(redacted_query, top_k=3)
    resolved_slug = retrieval_res["resolved_scheme"]
    chunks = retrieval_res["chunks"]

    # Load resolved scheme metadata if available
    resolved_metadata = None
    if resolved_slug and retriever.schemes_meta:
        for s in retriever.schemes_meta:
            if s["slug"] == resolved_slug:
                json_path = retriever.processed_dir / f"{resolved_slug}.json"
                if json_path.exists():
                    try:
                        with open(json_path, "r", encoding="utf-8") as f:
                            json_data = json.load(f)
                            resolved_metadata = json_data.get("metadata")
                    except Exception as e:
                        print(f"Error loading scheme metadata file: {e}")
                break

    # Get primary citation and updated timestamp
    primary_citation = "https://groww.in"
    last_updated = "2026-06-17"
    if resolved_metadata:
        primary_citation = resolved_metadata.get("source_url", primary_citation)
        last_updated = resolved_metadata.get("last_updated", last_updated)

    # 4. Generate Answer
    try:
        raw_answer = generator.generate(redacted_query, resolved_metadata, chunks)
    except Exception as e:
        print(f"LLM generation failed: {e}")
        # Return fallback response on LLM failure
        return QueryResponse(
            answer="Information not found in official source files.",
            citation_url=primary_citation,
            last_updated=last_updated,
            is_refusal=False,
            disclaimer="Facts-only. No investment advice."
        )

    # 5. Validate Answer
    context_str = generator.build_context_string(resolved_metadata, chunks)
    answer, citation, is_refusal = validator.validate(raw_answer, context_str, primary_citation)

    # 6. Format Output
    response_payload = formatter.format_response(answer, citation, last_updated, is_refusal)
    return QueryResponse(
        answer=response_payload["answer"],
        citation_url=response_payload["citation_url"],
        last_updated=response_payload["last_updated"],
        is_refusal=response_payload["is_refusal"],
        disclaimer=response_payload["disclaimer"]
    )

# Serve the static UI files
# Make sure the 'ui' directory exists
os.makedirs("ui", exist_ok=True)
app.mount("/ui", StaticFiles(directory="ui", html=True), name="ui")

@app.get("/")
async def root():
    return RedirectResponse(url="/ui/index.html")
