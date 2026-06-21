import json
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer

# Paths relative to the Week 8 project root directory
BASE_DIR = Path(__file__).resolve().parent.parent
INDEX_DIR = BASE_DIR / "data" / "index"

def verify():
    print("==========================================")
    print("VERIFYING CHROMADB SEARCH FUNCTIONALITY")
    print("==========================================")

    if not INDEX_DIR.exists():
        print(f"Error: Vector index directory does not exist at {INDEX_DIR}")
        return

    print("Connecting to local ChromaDB client...")
    client = chromadb.PersistentClient(path=str(INDEX_DIR))
    
    collection_name = "hdfc_faq_collection"
    try:
        collection = client.get_collection(name=collection_name)
        print(f"Successfully connected to collection: {collection_name}")
        print(f"Total documents in collection: {collection.count()}")
    except Exception as e:
        print(f"Error: Could not retrieve collection '{collection_name}': {e}")
        return

    # Initialize model to embed search query
    model_name = 'BAAI/bge-small-en-v1.5'
    print(f"Loading embedding model: {model_name}...")
    model = SentenceTransformer(model_name)

    query = "Who is the fund manager of HDFC Mid Cap?"
    print(f"\nQuery: '{query}'")
    
    # Query context format
    query_vector = model.encode(query).tolist()
    
    print("Performing vector search...")
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=3
    )

    print("\n--- Top Search Results ---")
    for idx in range(len(results["ids"][0])):
        doc_id = results["ids"][0][idx]
        doc_text = results["documents"][0][idx]
        metadata = results["metadatas"][0][idx]
        distance = results["distances"][0][idx]
        
        print(f"\n[{idx+1}] ID: {doc_id} (Distance: {distance:.4f})")
        print(f"Scheme: {metadata.get('scheme_name')}")
        print(f"Section: {metadata.get('section')}")
        print(f"URL: {metadata.get('source_url')}")
        print(f"Content: {doc_text[:180]}...")
    print("==========================================")

if __name__ == "__main__":
    verify()
