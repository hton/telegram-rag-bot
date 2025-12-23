"""Fetch full document context for selected sources"""
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from loguru import logger

from src.core.config import settings
from src.core.exceptions import RetrievalError


class RetrievalEnhancer:
    """
    Fetch full document context for selected source_path values

    Matches n8n workflow:
    - "Postgres3" node
    - Groups documents by source_path
    - Aggregates all text chunks with same heading
    - Returns structured context
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.table_name = settings.VECTOR_TABLE

    async def fetch_full_documents(
        self,
        source_paths: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Fetch full document data for given source_path values

        Args:
            source_paths: List of source_path values from reranking

        Returns:
            List of documents grouped by source_path with aggregated content

        Raises:
            RetrievalError: If retrieval fails
        """
        try:
            if not source_paths:
                return []

            # SQL query matching n8n "Postgres3" node
            # Groups by source_path, aggregates all chunks with their headings
            query = text(f"""
                SELECT
                  source_path,
                  ARRAY_AGG(
                    jsonb_build_object(
                      'title', title,
                      'heading', heading,
                      'text', text
                    ) ORDER BY position ASC
                  ) AS grouped_items
                FROM (
                  SELECT DISTINCT ON (source_path, heading) *
                  FROM {self.table_name}
                  WHERE source_path = ANY(:source_paths)
                  ORDER BY source_path, heading, position
                ) AS sub
                GROUP BY source_path
                LIMIT 5;
            """)

            result = await self.db.execute(
                query,
                {"source_paths": source_paths}
            )

            rows = result.fetchall()

            documents = []
            for row in rows:
                documents.append({
                    "source_path": row.source_path,
                    "grouped_items": row.grouped_items,
                })

            logger.info(f"Fetched full context for {len(documents)} source documents")
            return documents

        except Exception as e:
            logger.error(f"Failed to fetch full documents: {e}")
            raise RetrievalError(f"Failed to fetch full documents: {e}")

    def aggregate_context(self, documents: List[Dict[str, Any]]) -> str:
        """
        Aggregate full documents into context string for LLM

        Format matches n8n "Aggregate1" node output

        Args:
            documents: List of documents with grouped items

        Returns:
            Formatted context string
        """
        if not documents:
            return ""

        context_parts = []

        for doc in documents:
            source_path = doc["source_path"]
            items = doc["grouped_items"]

            # Format each source document
            doc_text = f"\n{'='*80}\nИсточник: {source_path}\n{'='*80}\n"

            for item in items:
                if item.get("title"):
                    doc_text += f"\n# {item['title']}\n"
                if item.get("heading"):
                    doc_text += f"\n## {item['heading']}\n"
                doc_text += f"\n{item['text']}\n"

            context_parts.append(doc_text)

        aggregated = "\n".join(context_parts)
        logger.debug(f"Aggregated context length: {len(aggregated)} characters")

        return aggregated
