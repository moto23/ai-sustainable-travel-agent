import logging
import os
from rag_system.data_processor import DataProcessor
from rag_system.embeddings_generator import EmbeddingsGenerator
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KnowledgeBaseBuilder:
    """
    Automates the pipeline: scrape/process data, generate embeddings, validate, and log.
    """
    def __init__(self, sources, kb_path, emb_path):
        self.sources = sources
        self.kb_path = kb_path
        self.emb_path = emb_path

    def build(self):
        # Step 1: Scrape and process data
        processor = DataProcessor(self.sources)
        processor.scrape()
        processed = processor.process()
        processor.save(processed, self.kb_path)
        logger.info("Data scraping and processing complete.")

        # Step 2: Validate processed data
        self.validate_data(self.kb_path)

        # Step 3: Generate embeddings
        generator = EmbeddingsGenerator()
        docs = generator.load_knowledge_base(self.kb_path)
        docs_with_emb = generator.generate_embeddings(docs)
        generator.save_embeddings(docs_with_emb, self.emb_path)
        logger.info("Embeddings generation complete.")

        # Step 4: Validate embeddings
        self.validate_embeddings(self.emb_path)

    def validate_data(self, kb_path):
        logger.info("Validating processed data...")
        with open(kb_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                doc = json.loads(line)
                assert 'text' in doc and doc['text'], f"Missing text in doc {i}"
                assert 'metadata' in doc, f"Missing metadata in doc {i}"
                meta = doc['metadata']
                assert 'location' in meta, f"Missing location in metadata {i}"
                assert 'category' in meta, f"Missing category in metadata {i}"
                assert 'sustainability_score' in meta, f"Missing sustainability_score in metadata {i}"
        logger.info("Data validation passed.")

    def validate_embeddings(self, emb_path):
        logger.info("Validating embeddings...")
        with open(emb_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                doc = json.loads(line)
                assert 'embedding' in doc, f"Missing embedding in doc {i}"
                assert isinstance(doc['embedding'], list), f"Embedding is not a list in doc {i}"
        logger.info("Embeddings validation passed.")

if __name__ == "__main__":
    sources = [
        "https://www.example.com/eco-hotel",
        "https://www.example.com/green-transport"
    ]
    kb_path = "rag_system/sample_knowledge_base.jsonl"
    emb_path = "rag_system/knowledge_base_with_embeddings.jsonl"
    builder = KnowledgeBaseBuilder(sources, kb_path, emb_path)
    builder.build()
