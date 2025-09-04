import json
import logging
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingsGenerator:
    """
    Generates embeddings for knowledge base documents using sentence-transformers.
    """
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)

    def load_knowledge_base(self, kb_path: str) -> List[Dict[str, Any]]:
        docs = []
        with open(kb_path, 'r', encoding='utf-8') as f:
            for line in f:
                docs.append(json.loads(line))
        logger.info(f"Loaded {len(docs)} documents from {kb_path}")
        return docs

    def generate_embeddings(self, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        texts = [doc['text'] for doc in docs]
        logger.info(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = self.model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
        for i, doc in enumerate(docs):
            doc['embedding'] = embeddings[i].tolist()
        logger.info("Embeddings generated.")
        return docs

    def save_embeddings(self, docs: List[Dict[str, Any]], out_path: str):
        with open(out_path, 'w', encoding='utf-8') as f:
            for doc in docs:
                f.write(json.dumps(doc) + '\n')
        logger.info(f"Saved embeddings to {out_path}")

if __name__ == "__main__":
    kb_path = "rag_system/sample_knowledge_base.jsonl"
    out_path = "rag_system/knowledge_base_with_embeddings.jsonl"
    generator = EmbeddingsGenerator()
    docs = generator.load_knowledge_base(kb_path)
    docs_with_emb = generator.generate_embeddings(docs)
    generator.save_embeddings(docs_with_emb, out_path)
