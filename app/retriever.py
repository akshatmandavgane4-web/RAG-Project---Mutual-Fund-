import re
import json
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from sentence_transformers import SentenceTransformer

# Paths relative to the Week 8 project root directory
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "corpus.yaml"
INDEX_DIR = BASE_DIR / "data" / "index"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

class RAGRetriever:
    def __init__(self, config_path: Path = CONFIG_PATH, index_dir: Path = INDEX_DIR, processed_dir: Path = PROCESSED_DIR):
        self.config_path = config_path
        self.index_dir = index_dir
        self.processed_dir = processed_dir
        self.model_name = 'BAAI/bge-small-en-v1.5'
        self.collection_name = "hdfc_faq_collection"
        
        # Load corpus configuration for scheme mappings
        self.schemes_meta = []
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
                self.schemes_meta = config_data.get("schemes", [])

        # Setup local Chroma client
        self.client = chromadb.PersistentClient(path=str(self.index_dir))
        
        # Setup local embedding model
        print(f"Retriever loading embedding model: {self.model_name}...")
        self.model = SentenceTransformer(self.model_name)

        # Keyword mapping to resolve target schemes
        self.resolution_rules = {
            "hdfc-mid-cap-fund-direct-growth": ["mid cap", "midcap", "mid-cap"],
            "hdfc-large-cap-fund-direct-growth": ["large cap", "largecap", "large-cap"],
            "hdfc-small-cap-fund-direct-growth": ["small cap", "smallcap", "small-cap"],
            "hdfc-gold-etf-fund-of-fund-direct-plan-growth": ["gold", "etf", "gold fof"],
            "hdfc-defence-fund-direct-growth": ["defence", "defense", "sectoral"]
        }

    def resolve_scheme(self, query: str) -> Optional[str]:
        # Match query tokens to map to a single target mutual fund slug
        query_lower = query.lower()
        for slug, keywords in self.resolution_rules.items():
            for kw in keywords:
                if kw in query_lower:
                    return slug
        return None

    def retrieve(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        # 1. Scheme Resolution
        resolved_slug = self.resolve_scheme(query)
        
        # 2. Get collection
        try:
            collection = self.client.get_collection(name=self.collection_name)
        except Exception as e:
            print(f"Error connecting to collection '{self.collection_name}': {e}")
            return {"chunks": [], "resolved_scheme": None}

        # 3. Vector Embed Query
        query_vector = self.model.encode(query).tolist()

        # 4. Prepare Metadata Filter
        where_filter = None
        if resolved_slug:
            where_filter = {"scheme_slug": resolved_slug}

        # 5. Query Vector Database
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=top_k * 2 if resolved_slug else top_k,  # Fetch more candidate chunks to support section boosting
            where=where_filter
        )

        if not results or not results["documents"] or not results["documents"][0]:
            return {"chunks": [], "resolved_scheme": resolved_slug}

        # 6. Parse and Structure Candidates
        candidates = []
        for i in range(len(results["ids"][0])):
            candidates.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            })

        # 7. Apply Section Boosting
        # If the query contains section keywords, prioritize those sections
        query_lower = query.lower()
        boosted_section = None
        if any(w in query_lower for w in ["manager", "manage", "experience", "education", "tenure"]):
            boosted_section = "fund_management"
        elif any(w in query_lower for w in ["exit load", "redeem", "redemption"]):
            boosted_section = "exit_load"
        elif any(w in query_lower for w in ["expense ratio", "ratio", "fee"]):
            boosted_section = "expense_ratio"
        elif any(w in query_lower for w in ["sip", "minimum", "lumpsum"]):
            boosted_section = "minimum_investment"

        if boosted_section:
            # Sort candidates with boosted_section first, maintaining relative distance ordering
            boosted_chunks = [c for c in candidates if c["metadata"].get("section") == boosted_section]
            other_chunks = [c for c in candidates if c["metadata"].get("section") != boosted_section]
            candidates = boosted_chunks + other_chunks

        # Return top-k chunks
        return {
            "chunks": candidates[:top_k],
            "resolved_scheme": resolved_slug
        }

if __name__ == "__main__":
    retriever = RAGRetriever()
    res = retriever.retrieve("Who is the fund manager of HDFC Mid Cap?")
    print("Resolved Scheme:", res["resolved_scheme"])
    print("Top Chunks retrieved:")
    for c in res["chunks"]:
        print(f"- Section: {c['metadata']['section']}, Distance: {c['distance']:.4f}, Text: {c['text'][:100]}...")
