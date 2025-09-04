import os
import pinecone
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PineconeManager:
    """
    Async manager for Pinecone vector database integration.
    Supports index creation, upsert, query, delete, batch processing, semantic search, backup/restore.
    """
    def __init__(self, api_key: str, environment: str, index_name: str, dimension: int):
        self.api_key = api_key
        self.environment = environment
        self.index_name = index_name
        self.dimension = dimension
        self.index = None
        pinecone.init(api_key=api_key, environment=environment)

    async def create_index(self, metric: str = "cosine"):
        if self.index_name not in pinecone.list_indexes():
            pinecone.create_index(self.index_name, dimension=self.dimension, metric=metric)
            logger.info(f"Created Pinecone index: {self.index_name}")
        self.index = pinecone.Index(self.index_name)

    async def upsert_vectors(self, vectors: List[Dict[str, Any]], batch_size: int = 100):
        """Upsert vectors in batches."""
        if not self.index:
            self.index = pinecone.Index(self.index_name)
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i+batch_size]
            ids = [v['id'] for v in batch]
            embeds = [v['embedding'] for v in batch]
            meta = [v['metadata'] for v in batch]
            to_upsert = list(zip(ids, embeds, meta))
            self.index.upsert(vectors=to_upsert)
            logger.info(f"Upserted batch {i//batch_size+1} of {len(vectors)//batch_size+1}")

    async def query(self, query_vector: List[float], top_k: int = 10, filters: Optional[Dict[str, Any]] = None, similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        if not self.index:
            self.index = pinecone.Index(self.index_name)
        query_kwargs = {
            "vector": query_vector,
            "top_k": top_k,
            "include_metadata": True
        }
        if filters:
            query_kwargs["filter"] = filters
        results = self.index.query(**query_kwargs)
        # Filter by similarity threshold and rank
        matches = [m for m in results.matches if m.score >= similarity_threshold]
        matches.sort(key=lambda x: x.score, reverse=True)
        logger.info(f"Query returned {len(matches)} results above threshold {similarity_threshold}")
        return [{"id": m.id, "score": m.score, "metadata": m.metadata} for m in matches]

    async def delete(self, ids: List[str]):
        if not self.index:
            self.index = pinecone.Index(self.index_name)
        self.index.delete(ids)
        logger.info(f"Deleted {len(ids)} vectors from index {self.index_name}")

    async def backup_index(self, backup_path: str):
        """Backup index metadata and IDs (not embeddings)."""
        if not self.index:
            self.index = pinecone.Index(self.index_name)
        stats = self.index.describe_index_stats()
        ids = list(stats['namespaces']['']['vector_count'])
        with open(backup_path, 'w', encoding='utf-8') as f:
            for id in ids:
                meta = self.index.fetch([id]).vectors[id].metadata
                f.write(f"{id}\t{meta}\n")
        logger.info(f"Backed up index metadata to {backup_path}")

    async def restore_index(self, backup_path: str):
        """Restore index metadata from backup (stub, as embeddings are not stored)."""
        # In real use, you would need to re-upsert embeddings as well
        logger.info(f"Restore from {backup_path} is a stub (embeddings not included in backup)")

    async def close(self):
        # Pinecone Python client does not require explicit close, but for aiohttp or other clients, close here
        pass

# Example usage (async):
# async def main():
#     manager = PineconeManager(api_key, environment, index_name, dimension)
#     await manager.create_index()
#     await manager.upsert_vectors(vectors)
#     results = await manager.query(query_vector, filters={"location": "Berlin"})
#     await manager.delete(["id1", "id2"])
#     await manager.backup_index("backup.txt")
#     await manager.restore_index("backup.txt")
