"""Vector similarity search using pgvector"""
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from loguru import logger

from src.core.config import settings
from src.core.exceptions import RetrievalError


class VectorRetriever:
    """
    Vector similarity search using pgvector

    Matches the n8n workflow:
    1. Embed query
    2. Search in pgvector table (top K results by cosine distance)
    3. Return structured results
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.table_name = settings.VECTOR_TABLE
        self.top_k = settings.TOP_K_RESULTS

    async def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search

        Args:
            query_embedding: Query embedding vector (1536 dimensions for ada-002)
            top_k: Number of results to return (default: from config)

        Returns:
            List of documents with similarity scores

        Raises:
            RetrievalError: If retrieval fails
        """
        try:
            top_k = top_k or self.top_k

            # Convert embedding to string format for pgvector
            embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

            # SQL query matching the n8n workflow
            query = text(f"""
                SELECT
                    id,
                    source_path,
                    title,
                    heading,
                    text,
                    position,
                    metadata,
                    embedding <=> :embedding::vector AS distance
                FROM {self.table_name}
                ORDER BY distance
                LIMIT :limit
            """)

            result = await self.db.execute(
                query,
                {"embedding": embedding_str, "limit": top_k}
            )

            rows = result.fetchall()

            documents = []
            for row in rows:
                documents.append({
                    "id": row.id,
                    "source_path": row.source_path,
                    "title": row.title,
                    "heading": row.heading,
                    "text": row.text,
                    "position": row.position,
                    "metadata": row.metadata or {},
                    "distance": float(row.distance),
                })

            logger.info(f"Retrieved {len(documents)} documents from vector search")
            return documents

        except Exception as e:
            logger.error(f"Vector retrieval failed: {e}")
            raise RetrievalError(f"Failed to retrieve documents: {e}")
