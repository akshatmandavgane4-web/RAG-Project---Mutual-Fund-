import re
import json
import yaml
from pathlib import Path

# Paths relative to the Week 8 project root directory
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "corpus.yaml"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

class Chunker:
    def __init__(self, config_path: Path = CONFIG_PATH, processed_dir: Path = PROCESSED_DIR):
        self.config_path = config_path
        self.processed_dir = processed_dir

    def load_config(self) -> dict:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def split_text_recursive(self, text: str, max_words: int = 250, overlap_words: int = 50) -> list:
        # Simple recursive-like word splitter respecting sentences first, then spaces
        sentences = re.split(r'(?<=[.!?]) +', text)
        chunks = []
        current_chunk = []
        current_word_count = 0

        for sentence in sentences:
            sentence_words = sentence.split()
            sentence_word_count = len(sentence_words)
            
            if current_word_count + sentence_word_count <= max_words:
                current_chunk.append(sentence)
                current_word_count += sentence_word_count
            else:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                # Retain overlap words
                overlap_text = []
                overlap_count = 0
                for s in reversed(current_chunk):
                    s_words = s.split()
                    if overlap_count + len(s_words) <= overlap_words:
                        overlap_text.insert(0, s)
                        overlap_count += len(s_words)
                    else:
                        break
                current_chunk = overlap_text + [sentence]
                current_word_count = overlap_count + sentence_word_count

        if current_chunk:
            chunks.append(" ".join(current_chunk))
        return chunks

    def chunk_section(self, section_tag: str, text: str, scheme_name: str, managers: list) -> list:
        if not text or not text.strip():
            return []

        # Keep small sections as a single chunk
        single_chunk_sections = ["expense_ratio", "exit_load", "minimum_investment", "benchmark", "tax", "investment_objective"]
        if section_tag in single_chunk_sections:
            return [text.strip()]

        # Split fund management by individual manager names
        if section_tag == "fund_management" and managers:
            manager_chunks = []
            manager_names = [m["name"] for m in managers if m.get("name") and m["name"] != "N/A"]
            
            if manager_names:
                # Find occurrences of manager names to split text
                positions = []
                for name in manager_names:
                    # Find all matches of manager name
                    for m in re.finditer(re.escape(name), text):
                        positions.append((m.start(), name))
                
                # Sort positions by start index
                positions.sort()
                
                if positions:
                    # Split text by manager index positions
                    for i in range(len(positions)):
                        start_pos = positions[i][0]
                        end_pos = positions[i+1][0] if i+1 < len(positions) else len(text)
                        chunk_text = text[start_pos:end_pos].strip()
                        
                        # If manager chunk is exceptionally large, split it further
                        if len(chunk_text.split()) > 300:
                            sub_chunks = self.split_text_recursive(chunk_text, max_words=250, overlap_words=50)
                            manager_chunks.extend(sub_chunks)
                        else:
                            manager_chunks.append(chunk_text)
                    return manager_chunks

        # Fallback recursive splitter for overview, fund_house, and large sections
        return self.split_text_recursive(text, max_words=250, overlap_words=50)

    def process_scheme(self, scheme_data: dict) -> list:
        metadata = scheme_data["metadata"]
        sections = scheme_data["sections"]
        scheme_name = metadata["name"]
        slug = metadata["id"]
        source_url = metadata["source_url"]
        managers = metadata.get("fund_managers", [])
        last_updated = metadata.get("last_updated", "2026-06-07")

        chunks = []
        for tag, text in sections.items():
            section_chunks = self.chunk_section(tag, text, scheme_name, managers)
            
            for idx, chunk_text in enumerate(section_chunks):
                # Prepend the contextual query schema header
                formatted_text = f"Scheme: {scheme_name} | Section: {tag} | Content: {chunk_text}"
                
                chunks.append({
                    "id": f"{slug}#{tag}#{idx}",
                    "text": chunk_text,
                    "formatted_text": formatted_text,
                    "scheme_name": scheme_name,
                    "scheme_slug": slug,
                    "source_url": source_url,
                    "section": tag,
                    "last_updated": last_updated
                })
        return chunks

    def run(self) -> list:
        try:
            config_data = self.load_config()
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return []

        schemes = config_data.get("schemes", [])
        all_chunks = []

        for scheme in schemes:
            slug = scheme["slug"]
            json_path = self.processed_dir / f"{slug}.json"
            
            if not json_path.exists():
                print(f"Parsed JSON file not found for {slug}, skipping chunking.")
                continue

            try:
                print(f"Chunking {json_path.name}...")
                with open(json_path, "r", encoding="utf-8") as f:
                    scheme_data = json.load(f)
                
                chunks = self.process_scheme(scheme_data)
                all_chunks.extend(chunks)
                print(f"Generated {len(chunks)} chunks for {slug}.")
            except Exception as e:
                print(f"Error processing chunks for {slug}: {e}")

        # Save to processed chunks file
        out_path = self.processed_dir / "chunks.json"
        with open(out_path, "w", encoding="utf-8") as out_f:
            json.dump(all_chunks, out_f, indent=2)
        print(f"Successfully chunked all files. Total chunks: {len(all_chunks)}. Saved to {out_path}")
        return all_chunks

if __name__ == "__main__":
    chunker = Chunker()
    chunker.run()
