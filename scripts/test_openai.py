#!/usr/bin/env python3
"""Test OpenAI API connectivity"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import settings
from src.core.logging import setup_logging
from openai import AsyncOpenAI
from loguru import logger


async def test_openai():
    """Test OpenAI API"""
    setup_logging()

    logger.info("Testing OpenAI API connectivity...")
    logger.info(f"Model: {settings.LLM_MODEL}")
    logger.info(f"Embedding Model: {settings.EMBEDDING_MODEL}")

    try:
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL)

        # Test embeddings
        logger.info("Testing embeddings...")
        embedding_response = await client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input="test query",
        )
        embedding = embedding_response.data[0].embedding
        logger.info(f"✅ Embeddings working! Dimension: {len(embedding)}")

        # Test completions
        logger.info("Testing completions...")
        completion_response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "user", "content": "Say 'test successful'"}
            ],
            max_tokens=10,
        )
        answer = completion_response.choices[0].message.content
        logger.info(f"✅ Completions working! Response: {answer}")

        logger.info("✅ All OpenAI tests passed!")
        return True

    except Exception as e:
        logger.error(f"❌ OpenAI test failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_openai())
    sys.exit(0 if success else 1)
