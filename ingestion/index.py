import json
import yaml
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer
from datetime import datetime

# Paths relative to the Week 8 project root directory
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "corpus.yaml"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
INDEX_DIR = BASE_DIR / "data" / "index"

class Indexer:
    def __init__(self, config_path: Path = CONFIG_PATH, processed_dir: Path = PROCESSED_DIR, index_dir: Path = INDEX_DIR):
        self.config_path = config_path
        self.processed_dir = processed_dir
        self.index_dir = index_dir
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.model_name = 'BAAI/bge-small-en-v1.5'

    def load_chunks(self) -> list:
        chunks_path = self.processed_dir / "chunks.json"
        if not chunks_path.exists():
            raise FileNotFoundError(f"Chunks file not found: {chunks_path}")
        with open(chunks_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_config(self) -> dict:
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def run(self):
        print(f"Loading chunks for indexing...")
        try:
            chunks = self.load_chunks()
        except Exception as e:
            print(f"Error loading chunks: {e}")
            return

        if not chunks:
            print("No chunks found to index!")
            return

        print(f"Initializing local embedding model: {self.model_name}...")
        model = SentenceTransformer(self.model_name)

        print("Computing embeddings...")
        # Embed the contextual formatted text for rich semantic representations
        texts_to_embed = [chunk["formatted_text"] for chunk in chunks]
        embeddings = model.encode(texts_to_embed, show_progress_bar=True).tolist()

        print("Initializing ChromaDB collection...")
        client = chromadb.PersistentClient(path=str(self.index_dir))
        
        # Reset / recreate collection to prevent duplicate accumulation
        collection_name = "hdfc_faq_collection"
        try:
            client.delete_collection(name=collection_name)
            print(f"Deleted existing collection: {collection_name}")
        except Exception:
            pass
            
        collection = client.create_collection(name=collection_name)

        ids = [chunk["id"] for chunk in chunks]
        documents = [chunk["text"] for chunk in chunks]
        metadatas = []
        
        for chunk in chunks:
            metadatas.append({
                "source_url": chunk["source_url"],
                "scheme_name": chunk["scheme_name"],
                "scheme_slug": chunk["scheme_slug"],
                "section": chunk["section"],
                "last_updated": chunk["last_updated"],
                "formatted_text": chunk["formatted_text"]
            })

        print(f"Adding {len(ids)} chunks to ChromaDB collection...")
        collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )
        print("Indexing completed successfully!")

        # Update metadata JSON index with run stats
        try:
            config_data = self.load_config()
            metadata_index_path = self.processed_dir / "metadata_index.json"
            
            metadata_entries = {}
            for scheme in config_data.get("schemes", []):
                slug = scheme["slug"]
                # Resolve scheme details from parsed file
                json_path = self.processed_dir / f"{slug}.json"
                if json_path.exists():
                    with open(json_path, "r", encoding="utf-8") as f:
                        scheme_info = json.load(f)
                    metadata_entries[slug] = scheme_info["metadata"]
            
            with open(metadata_index_path, "w", encoding="utf-8") as meta_f:
                json.dump({
                    "last_indexed_at": datetime.today().strftime("%Y-%m-%d"),
                    "collection_name": collection_name,
                    "model_name": self.model_name,
                    "schemes": metadata_entries
                }, meta_f, indent=2)
            print(f"Metadata index successfully updated at {metadata_index_path}")
        except Exception as e:
            print(f"Error writing metadata index: {e}")

if __name__ == "__main__":
    indexer = Indexer()
    indexer.run()
