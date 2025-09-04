import asyncio
import os
import random
from rag_system.vector_store import PineconeManager

API_KEY = os.getenv("PINECONE_API_KEY", "test-key")
ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "test-env")
INDEX_NAME = "test-index"
DIMENSION = 8  # Use small dimension for test

async def test_pinecone_manager():
    manager = PineconeManager(API_KEY, ENVIRONMENT, INDEX_NAME, DIMENSION)
    await manager.create_index()

    # Create mock vectors
    vectors = [
        {
            "id": f"vec_{i}",
            "embedding": [random.random() for _ in range(DIMENSION)],
            "metadata": {"location": "Berlin", "category": "eco_hotel", "price_range": "mid"}
        }
        for i in range(20)
    ]
    await manager.upsert_vectors(vectors, batch_size=5)

    # Query
    query_vector = vectors[0]["embedding"]
    results = await manager.query(query_vector, top_k=5, filters={"location": "Berlin"}, similarity_threshold=0.0)
    print(f"Query results: {results}")
    assert len(results) > 0

    # Delete
    ids_to_delete = [vectors[0]["id"]]
    await manager.delete(ids_to_delete)
    print(f"Deleted ids: {ids_to_delete}")

    # Backup/restore
    backup_path = "test_index_backup.txt"
    await manager.backup_index(backup_path)
    await manager.restore_index(backup_path)
    print(f"Backup and restore tested.")

    await manager.close()

if __name__ == "__main__":
    asyncio.run(test_pinecone_manager())
