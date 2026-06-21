import os
import time
import requests
import yaml
from pathlib import Path

# Paths relative to the Week 8 project root directory
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "corpus.yaml"
RAW_DIR = BASE_DIR / "data" / "raw"

class Fetcher:
    def __init__(self, config_path: Path = CONFIG_PATH, raw_dir: Path = RAW_DIR):
        self.config_path = config_path
        self.raw_dir = raw_dir
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
        }

    def load_urls(self) -> list:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
        return config_data.get("schemes", [])

    def fetch_url(self, url: str, slug: str) -> Path:
        target_path = self.raw_dir / f"{slug}.html"
        print(f"Fetching {url}...")
        
        # 3 Retries with backoff as per ING-01
        retries = 3
        backoff = 2
        for attempt in range(1, retries + 1):
            try:
                response = requests.get(url, headers=self.headers, timeout=15)
                response.raise_for_status()
                
                # Check for empty content
                if not response.content:
                    raise ValueError(f"Empty HTML content received from {url}")
                
                # Write raw HTML content to file
                target_path.write_bytes(response.content)
                print(f"Successfully saved to {target_path}")
                return target_path
            except Exception as e:
                print(f"Attempt {attempt}/{retries} failed for {url}: {e}")
                if attempt == retries:
                    raise
                time.sleep(backoff)
                backoff *= 2

    def run(self) -> dict:
        results = {}
        try:
            schemes = self.load_urls()
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return results

        for scheme in schemes:
            url = scheme.get("source_url")
            slug = scheme.get("slug")
            if not url or not slug:
                print(f"Skipping invalid scheme configuration: {scheme}")
                continue
            
            try:
                path = self.fetch_url(url, slug)
                results[slug] = path
                time.sleep(2)  # Politeness delay
            except Exception as e:
                print(f"Critical error: Failed to fetch {url}: {e}")
        return results

if __name__ == "__main__":
    fetcher = Fetcher()
    fetcher.run()
