"""Answer generation using OpenAI LLM"""
from typing import List, Dict, Any
from openai import AsyncOpenAI
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import settings
from src.core.exceptions import GenerationError
from src.rag.prompts import SYSTEM_PROMPT_TEMPLATE
from src.core.metrics import openai_api_calls, openai_tokens_used


class AnswerGenerator:
    """
    Answer generator using OpenAI GPT-4o-mini

    Generates answers based on retrieved context and chat history
    """

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.LLM_MODEL
        self.temperature = settings.TEMPERATURE
        self.max_tokens = settings.MAX_TOKENS

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def generate_answer(
        self,
        question: str,
        context: str,
        chat_history: List[Dict[str, str]] = None,
    ) -> str:
        """
        Generate answer using LLM

        Args:
            question: User's question
            context: Retrieved documentation context
            chat_history: Optional chat history for context

        Returns:
            Generated answer text

        Raises:
            GenerationError: If answer generation fails
        """
        try:
            # Build system prompt with context
            system_prompt = SYSTEM_PROMPT_TEMPLATE.format(question=question)
            system_prompt += f"\n\n{context}"

            # Build messages
            messages = [
                {"role": "system", "content": system_prompt}
            ]

            # Add chat history if available
            if chat_history:
                for msg in chat_history[-settings.CONTEXT_WINDOW:]:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })

            # Add current question
            messages.append({
                "role": "user",
                "content": question
            })

            logger.debug(f"Generating answer for question: {question[:100]}...")

            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            answer = response.choices[0].message.content

            # Log and track token usage
            usage = response.usage
            logger.info(
                f"Answer generated. Tokens: {usage.total_tokens} "
                f"(prompt: {usage.prompt_tokens}, completion: {usage.completion_tokens})"
            )

            # Track metrics
            openai_api_calls.labels(model=self.model, operation="completion").inc()
            openai_tokens_used.labels(
                model=self.model,
                token_type="prompt"
            ).inc(usage.prompt_tokens)
            openai_tokens_used.labels(
                model=self.model,
                token_type="completion"
            ).inc(usage.completion_tokens)

            return answer

        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            raise GenerationError(f"Failed to generate answer: {e}")
