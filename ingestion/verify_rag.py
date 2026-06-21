import os
import sys
from pathlib import Path

# Ensure project root is in python path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.classifier import QueryClassifier
from app.retriever import RAGRetriever
from app.generator import RAGGenerator
from app.validator import ResponseValidator
from app.formatter import ResponseFormatter

def run_rag_query(query: str):
    print(f"\nUser Query: '{query}'")
    
    classifier = QueryClassifier()
    retriever = RAGRetriever()
    generator = RAGGenerator()
    validator = ResponseValidator()
    formatter = ResponseFormatter()

    # 1. PII Scan
    is_pii, redacted_query = classifier.scan_for_pii(query)
    if is_pii:
        res = classifier.handle_refusal("factual", pii_detected=True)
        print("PII Refusal Triggered:")
        print(res)
        return res

    # 2. Intent Classification
    intent = classifier.classify_intent(redacted_query)
    if intent != "factual":
        res = classifier.handle_refusal(intent)
        print(f"Compliance Refusal Triggered (Intent: {intent}):")
        print(res)
        return res

    # 3. Retrieve Context
    retrieval_res = retriever.retrieve(redacted_query, top_k=3)
    resolved_slug = retrieval_res["resolved_scheme"]
    chunks = retrieval_res["chunks"]

    # Load resolved scheme metadata if available
    resolved_metadata = None
    if resolved_slug and retriever.schemes_meta:
        for s in retriever.schemes_meta:
            if s["slug"] == resolved_slug:
                # Load fully parsed data
                json_path = retriever.processed_dir / f"{resolved_slug}.json"
                if json_path.exists():
                    import json
                    with open(json_path, "r", encoding="utf-8") as f:
                        json_data = json.load(f)
                        resolved_metadata = json_data.get("metadata")
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
        return

    # 5. Validate Answer
    context_str = generator.build_context_string(resolved_metadata, chunks)
    answer, citation, is_refusal = validator.validate(raw_answer, context_str, primary_citation)

    # 6. Format Output
    response_payload = formatter.format_response(answer, citation, last_updated, is_refusal)
    print("Successful RAG Response Payload:")
    print(response_payload)
    return response_payload

if __name__ == "__main__":
    # Test Factual Query
    run_rag_query("What is the expense ratio of HDFC Mid Cap Fund?")
    
    # Test Advisory Query
    run_rag_query("Should I invest in HDFC Defence Fund?")
    
    # Test PII Query
    run_rag_query("My phone is +91 9876543210. Tell me about HDFC Large Cap expense ratio.")
