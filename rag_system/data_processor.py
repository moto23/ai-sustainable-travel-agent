import os
import re
import json
import logging
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHUNK_SIZE = 512  # tokens (approximate, by words for simplicity)

class DataProcessor:
    """
    Scrapes, cleans, chunks, and preprocesses eco-travel data from multiple sources.
    Extracts metadata: location, category, sustainability score.
    """
    def __init__(self, sources: List[str]):
        self.sources = sources
        self.documents = []

    def scrape(self):
        """Scrape data from all sources."""
        for url in self.sources:
            try:
                logger.info(f"Scraping {url}")
                resp = requests.get(url, timeout=10)
                soup = BeautifulSoup(resp.text, 'html.parser')
                # Example: extract all paragraphs
                text = ' '.join([p.get_text() for p in soup.find_all('p')])
                self.documents.append({"text": text, "source": url})
            except Exception as e:
                logger.error(f"Failed to scrape {url}: {e}")

    def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text

    def chunk_text(self, text: str) -> List[str]:
        """Chunk text into ~512 token (word) segments."""
        words = text.split()
        return [' '.join(words[i:i+CHUNK_SIZE]) for i in range(0, len(words), CHUNK_SIZE)]

    def extract_metadata(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from document (stub logic)."""
        # In real use, use NLP or regex to extract location/category/score
        return {
            "location": "Unknown",
            "category": "eco_hotel" if "hotel" in doc["text"].lower() else "other",
            "sustainability_score": 80  # Stub value
        }

    def process(self):
        """Clean, chunk, and extract metadata for all documents."""
        processed = []
        for doc in self.documents:
            clean = self.clean_text(doc["text"])
            chunks = self.chunk_text(clean)
            meta = self.extract_metadata(doc)
            for chunk in chunks:
                processed.append({
                    "text": chunk,
                    "metadata": meta,
                    "source": doc["source"]
                })
        logger.info(f"Processed {len(processed)} chunks from {len(self.documents)} documents.")
        return processed

    def save(self, processed: List[Dict[str, Any]], out_path: str):
        with open(out_path, 'w', encoding='utf-8') as f:
            for doc in processed:
                f.write(json.dumps(doc) + '\n')
        logger.info(f"Saved processed data to {out_path}")

if __name__ == "__main__":
    sources = [
        # Add real eco-travel URLs or use local HTML files for testing
        "https://www.example.com/eco-hotel",
        "https://www.example.com/green-transport"
    ]
    processor = DataProcessor(sources)
    processor.scrape()
    processed = processor.process()
    processor.save(processed, "rag_system/sample_knowledge_base.jsonl")
