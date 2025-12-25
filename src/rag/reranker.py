"""LLM-based reranking to select most relevant documents"""
from typing import List, Dict, Any
from openai import AsyncOpenAI
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import settings
from src.core.exceptions import RerankingError
from src.rag.prompts import RERANKING_SYSTEM_PROMPT, RERANKING_USER_PROMPT_TEMPLATE
from src.core.metrics import openai_api_calls, openai_tokens_used


class LLMReranker:
    """
    LLM-based reranking to select most relevant source documents

    Matches n8n workflow:
    - "Basic LLM Chain2" node
    - Uses GPT-4o-mini to analyze retrieved docs
    - Extracts top 5 source_path values
    """

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.LLM_MODEL

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def extract_top_sources(
        self,
        question: str,
        documents: List[Dict[str, Any]],
        top_k: int = None,
    ) -> List[str]:
        """
        Use LLM to select most relevant source_path values

        Args:
            question: User's question
            documents: Retrieved documents from vector search
            top_k: Number of source_path to return (default: from config)

        Returns:
            List of top source_path values

        Raises:
            RerankingError: If reranking fails
        """
        try:
            top_k = top_k or settings.RERANK_TOP_K

            # Format documents for LLM
            docs_context = "\n\n".join([
                f"Source: {doc['source_path']}\n"
                f"Title: {doc.get('title', 'N/A')}\n"
                f"Heading: {doc.get('heading', 'N/A')}\n"
                f"Text: {doc['text'][:250]}..."  # Truncate for token efficiency
                for doc in documents
            ])

            # Log first 3 documents to see what reranker is working with
            logger.info(f"Reranking {len(documents)} documents for question: '{question}'")
            logger.debug(f"First 3 documents:\n{docs_context[:800]}...")

            # Build messages
            messages = [
                {"role": "system", "content": RERANKING_SYSTEM_PROMPT},
                {"role": "user", "content": RERANKING_USER_PROMPT_TEMPLATE.format(
                    question=question,
                    documents=docs_context,
                    top_k=top_k,
                )}
            ]

            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.0,
                max_tokens=200,
            )

            # Track metrics
            openai_api_calls.labels(model=self.model, operation="reranking").inc()
            if hasattr(response, 'usage') and response.usage:
                openai_tokens_used.labels(
                    model=self.model,
                    token_type="prompt"
                ).inc(response.usage.prompt_tokens)
                openai_tokens_used.labels(
                    model=self.model,
                    token_type="completion"
                ).inc(response.usage.completion_tokens)

            # Parse response (comma-separated list)
            result_text = response.choices[0].message.content.strip()

            # Log raw LLM response for debugging (full response, not truncated)
            logger.info(f"Reranker LLM response (length={len(result_text)}): {result_text}")

            # Check if response is empty
            if not result_text:
                logger.warning("Reranker returned empty response! LLM may think no documents are relevant.")

            # Split by comma and clean
            source_paths = [s.strip() for s in result_text.split(",") if s.strip()]

            logger.debug(f"Parsed source_paths: {source_paths}")

            # Remove duplicates while preserving order
            unique_sources = []
            seen = set()
            for source in source_paths:
                if source and source not in seen:
                    unique_sources.append(source)
                    seen.add(source)

            # Limit to top_k
            top_sources = unique_sources[:top_k]

            logger.info(f"Reranked to {len(top_sources)} top source_path values: {top_sources}")

            # Warn if we got too few results
            if len(top_sources) < top_k:
                logger.warning(f"Reranker returned only {len(top_sources)} sources (expected {top_k})")

            return top_sources

        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            raise RerankingError(f"Failed to rerank documents: {e}")
