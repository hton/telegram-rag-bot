"""Answer generation using OpenAI LLM"""
from typing import List, Dict, Any, AsyncGenerator
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

    async def generate_answer_stream(
        self,
        question: str,
        context: str,
        chat_history: List[Dict[str, str]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Generate answer using LLM with streaming

        Args:
            question: User's question
            context: Retrieved documentation context
            chat_history: Optional chat history for context

        Yields:
            Chunks of generated answer text

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

            logger.debug(f"Generating answer (streaming) for question: {question[:100]}...")
            logger.info(f"API call params: model={self.model}, temperature={self.temperature}, max_tokens={self.max_tokens}")

            # Call OpenAI API with streaming
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True,  # Enable streaming
            )

            # Stream chunks and count tokens
            total_tokens_estimated = 0
            total_chars = 0
            finish_reason = None
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    total_tokens_estimated += len(content.split())
                    total_chars += len(content)
                    yield content
                # Capture finish reason
                if chunk.choices[0].finish_reason:
                    finish_reason = chunk.choices[0].finish_reason

            # Estimate tokens (rough: ~4 chars per token for English/Russian mix)
            completion_tokens_est = max(total_tokens_estimated, total_chars // 4)

            # Track metrics (estimated)
            openai_api_calls.labels(model=self.model, operation="completion_stream").inc()
            # Note: Prompt tokens estimation from message length
            prompt_tokens_est = sum(len(str(m.get('content', ''))) for m in messages) // 4
            openai_tokens_used.labels(
                model=self.model,
                token_type="prompt"
            ).inc(prompt_tokens_est)
            openai_tokens_used.labels(
                model=self.model,
                token_type="completion"
            ).inc(completion_tokens_est)

            logger.info(
                f"Answer streaming completed. Estimated tokens: ~{total_tokens_estimated} "
                f"(prompt: ~{prompt_tokens_est}, completion: ~{completion_tokens_est}), "
                f"finish_reason: {finish_reason}"
            )

        except Exception as e:
            logger.error(f"Error generating answer (streaming): {e}")
            raise GenerationError(f"Failed to generate answer: {e}")
