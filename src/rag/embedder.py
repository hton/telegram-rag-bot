"""OpenAI Embeddings Service"""
from typing import List, Tuple
from openai import AsyncOpenAI
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import settings
from src.core.exceptions import EmbeddingError
from src.core.metrics import openai_api_calls, openai_tokens_used


class OpenAIEmbedder:
    """
    OpenAI embeddings service using text-embedding-ada-002

    Generates 1536-dimensional embeddings for queries and documents
    """

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL)
        self.model = settings.EMBEDDING_MODEL
        self.dimensions = settings.EMBEDDING_DIMENSIONS

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def embed_query(self, text: str) -> Tuple[List[float], int]:
        """
        Generate embedding for a query text

        Args:
            text: Query text to embed

        Returns:
            Tuple of (embedding vector, tokens used)

        Raises:
            EmbeddingError: If embedding generation fails
        """
        try:
            # Prefix query for better retrieval (optional, can be configured)
            prefixed_text = f"search_query: {text.strip()}"

            logger.debug(f"Generating embedding for query: {text[:100]}...")

            response = await self.client.embeddings.create(
                model=self.model,
                input=prefixed_text,
                encoding_format="float",
            )

            embedding = response.data[0].embedding

            # Track metrics and get token usage
            openai_api_calls.labels(model=self.model, operation="embedding").inc()
            tokens_used = 0
            if hasattr(response, 'usage') and response.usage:
                tokens_used = response.usage.total_tokens
                openai_tokens_used.labels(
                    model=self.model,
                    token_type="prompt"
                ).inc(tokens_used)

            # Validate dimensions
            if len(embedding) != self.dimensions:
                raise EmbeddingError(
                    f"Expected {self.dimensions} dimensions, got {len(embedding)}"
                )

            logger.debug(f"Generated embedding with {len(embedding)} dimensions, {tokens_used} tokens")
            return embedding, tokens_used

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise EmbeddingError(f"Failed to generate embedding: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple documents (batch processing)

        Args:
            texts: List of document texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            logger.debug(f"Generating embeddings for {len(texts)} documents")

            # Batch API call (OpenAI supports batch embeddings)
            response = await self.client.embeddings.create(
                model=self.model,
                input=texts,
                encoding_format="float",
            )

            embeddings = [item.embedding for item in response.data]

            # Track metrics
            openai_api_calls.labels(model=self.model, operation="embedding").inc()
            if hasattr(response, 'usage') and response.usage:
                openai_tokens_used.labels(
                    model=self.model,
                    token_type="prompt"
                ).inc(response.usage.total_tokens)

            logger.debug(f"Generated {len(embeddings)} embeddings")
            return embeddings

        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise EmbeddingError(f"Failed to generate batch embeddings: {e}")
