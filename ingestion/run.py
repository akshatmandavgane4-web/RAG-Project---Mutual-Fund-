import os
import sys
from pathlib import Path

# Ensure project root is in python path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ingestion.fetch import Fetcher
from ingestion.parse import Parser
from ingestion.chunk import Chunker
from ingestion.index import Indexer

def main():
    print("==========================================")
    print("STARTING HDFC MF FAQ INGESTION PIPELINE")
    print("==========================================")
    
    # 1. Fetch
    print("\n--- STEP 1: FETCHING HTML PAGES ---")
    fetcher = Fetcher()
    fetcher.run()
    
    # 2. Parse
    print("\n--- STEP 2: PARSING DATA ---")
    parser = Parser()
    parser.run()
    
    # 3. Chunk
    print("\n--- STEP 3: SEMANTIC CHUNKING ---")
    chunker = Chunker()
    chunker.run()
    
    # 4. Index
    print("\n--- STEP 4: VECTOR STORE INDEXING ---")
    indexer = Indexer()
    indexer.run()
    
    print("\n==========================================")
    print("INGESTION PIPELINE COMPLETED SUCCESSFULLY!")
    print("==========================================")

if __name__ == "__main__":
    main()
