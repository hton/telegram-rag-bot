"""Unified query processing service"""
from typing import Optional, Dict, Any
import time
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from src.schemas.query import QueryResult
from src.schemas.enums import QuerySource
from src.rag.pipeline import RAGPipeline
from src.services.chat_memory import ChatMemoryService
from src.services.feedback import FeedbackService
from src.models.query_log import QueryLog
from src.core.metrics import query_counter, query_duration
from src.core.config import settings
from src.utils.cost_calculator import CostCalculator


class QueryService:
    """
    Unified service for processing queries from any source (Telegram, API, etc.)
    Handles RAG pipeline orchestration, memory, and feedback.
    """

    def __init__(
        self,
        db: AsyncSession,
        rag_pipeline: RAGPipeline,
        memory_service: ChatMemoryService,
        feedback_service: FeedbackService,
    ):
        self.db = db
        self.rag_pipeline = rag_pipeline
        self.memory_service = memory_service
        self.feedback_service = feedback_service

    async def process_query(
        self,
        question: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        source: QuerySource = QuerySource.API,
        enable_memory: bool = True,
        enable_feedback: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> QueryResult:
        """
        Process a query through the RAG pipeline

        Args:
            question: User's question
            user_id: User identifier (for memory and analytics)
            session_id: Session identifier (overrides user_id for memory)
            source: Query source (telegram/api)
            enable_memory: Whether to use chat history
            enable_feedback: Whether to enable feedback tracking
            metadata: Additional metadata

        Returns:
            QueryResult with answer and metadata
        """
        start_time = time.time()
        query_id = str(uuid.uuid4())

        logger.info(
            f"Processing query from {source}",
            query_id=query_id,
            user_id=user_id,
            question=question[:100],
        )

        try:
            # 1. Get chat history if enabled
            chat_history = []
            if enable_memory and (user_id or session_id):
                memory_key = session_id or user_id
                chat_history = await self.memory_service.get_history(memory_key)

            # 2. Run RAG pipeline
            rag_result = await self.rag_pipeline.run(
                question=question,
                chat_history=chat_history,
            )

            # 3. Update chat history
            if enable_memory and (user_id or session_id):
                memory_key = session_id or user_id
                await self.memory_service.add_message(memory_key, "user", question)
                # Save only summary to chat history for token efficiency
                await self.memory_service.add_assistant_message(memory_key, rag_result.answer)

            # 4. Calculate costs
            processing_time_ms = (time.time() - start_time) * 1000
            tokens_data = {
                "embedding": {"input": rag_result.tokens_used.embedding},
                "query_expansion": {
                    "input": rag_result.tokens_used.query_expansion_input,
                    "output": rag_result.tokens_used.query_expansion_output,
                },
                "reranking": {
                    "input": rag_result.tokens_used.reranking_input,
                    "output": rag_result.tokens_used.reranking_output,
                },
                "generation": {
                    "input": rag_result.tokens_used.generation_input,
                    "output": rag_result.tokens_used.generation_output,
                },
            }
            costs = CostCalculator.calculate_cost(tokens_data)

            # 5. Log query
            await self._log_query(
                query_id=query_id,
                question=question,
                answer=rag_result.answer,
                user_id=user_id,
                session_id=session_id,
                source=source,
                processing_time_ms=processing_time_ms,
                enable_feedback=enable_feedback,
                metadata=metadata or {},
            )

            # 6. Update metrics
            query_counter.labels(source=source.value).inc()
            query_duration.labels(source=source.value).observe(processing_time_ms / 1000)

            # 7. Return result
            return QueryResult(
                query_id=query_id,
                answer=rag_result.answer,
                sources=rag_result.sources,
                processing_time_ms=processing_time_ms,
                response_time_seconds=processing_time_ms / 1000,
                estimated_cost_usd=costs["usd"],
                estimated_cost_rub=costs["rub"],
                timestamp=datetime.utcnow(),
                context_used=rag_result.retrieved_docs,
            )

        except Exception as e:
            logger.error("Error processing query: {} (query_id: {})", e, query_id)
            raise

    async def _log_query(
        self,
        query_id: str,
        question: str,
        answer: str,
        user_id: Optional[str],
        session_id: Optional[str],
        source: QuerySource,
        processing_time_ms: float,
        enable_feedback: bool,
        metadata: Dict[str, Any],
    ):
        """Log query to database"""
        query_log = QueryLog(
            id=query_id,
            question=question,
            answer=answer,
            user_id=user_id,
            session_id=session_id,
            source=source.value,
            processing_time_ms=processing_time_ms,
            feedback_enabled=enable_feedback,
            query_metadata=metadata,
        )
        self.db.add(query_log)
        await self.db.commit()
