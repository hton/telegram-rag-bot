"""Query expansion using LLM to improve retrieval recall"""
from typing import Optional
from openai import AsyncOpenAI
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import settings
from src.core.exceptions import RAGPipelineError
from src.rag.prompts import QUERY_EXPANSION_SYSTEM_PROMPT, QUERY_EXPANSION_USER_PROMPT_TEMPLATE
from src.core.metrics import openai_api_calls, openai_tokens_used


class QueryExpander:
    """
    Expand user queries with synonyms, abbreviations, and related terms

    Uses LLM to enhance short queries and handle domain-specific terminology

    Benefits:
    - Handles abbreviations (ЗК → закрытый контур)
    - Adds synonyms and related terms
    - Improves recall for technical documentation

    Example:
        Input: "Как установить на ЗК?"
        Output: "Как установить на ЗК закрытый контур изолированная сеть
                 без интернета offline установка инсталляция ЕКП ISO образ"
    """

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.LLM_MODEL
        self.enabled = settings.QUERY_EXPANSION_ENABLED

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def expand_query(self, question: str) -> str:
        """
        Expand user query with related terms and synonyms

        Args:
            question: Original user question

        Returns:
            Expanded query string with additional terms

        Raises:
            RAGPipelineError: If expansion fails
        """
        try:
            if not self.enabled:
                logger.debug("Query expansion is disabled, returning original query")
                return question

            # Build messages
            messages = [
                {"role": "system", "content": QUERY_EXPANSION_SYSTEM_PROMPT},
                {"role": "user", "content": QUERY_EXPANSION_USER_PROMPT_TEMPLATE.format(
                    question=question
                )}
            ]

            logger.debug(f"Expanding query: {question[:100]}...")

            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.0,  # Changed from 0.3 to 0.0 for deterministic results
                max_tokens=150,
            )

            # Track metrics
            openai_api_calls.labels(model=self.model, operation="query_expansion").inc()
            if hasattr(response, 'usage') and response.usage:
                openai_tokens_used.labels(
                    model=self.model,
                    token_type="prompt"
                ).inc(response.usage.prompt_tokens)
                openai_tokens_used.labels(
                    model=self.model,
                    token_type="completion"
                ).inc(response.usage.completion_tokens)

            expanded_query = response.choices[0].message.content.strip()

            # Validate that original query is included
            if question.lower() not in expanded_query.lower():
                logger.warning("Expanded query doesn't include original, prepending it")
                expanded_query = f"{question} {expanded_query}"

            # Log full expanded query for debugging
            logger.info(f"Query expansion: '{question}' → '{expanded_query}'")

            return expanded_query

        except Exception as e:
            logger.error(f"Query expansion failed: {e}, using original query")
            # Fail gracefully - return original query
            return question

    async def expand_if_needed(self, question: str, min_length: int = 20) -> str:
        """
        Expand query only if it's short enough to benefit

        Args:
            question: Original user question
            min_length: Minimum length to trigger expansion

        Returns:
            Original or expanded query
        """
        if not self.enabled:
            return question

        # Skip expansion for already detailed queries
        if len(question) >= min_length:
            logger.debug(f"Query is long enough ({len(question)} chars), skipping expansion")
            return question

        return await self.expand_query(question)
