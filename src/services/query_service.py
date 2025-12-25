"""Unified query processing service"""
from typing import Optional, Dict, Any, AsyncGenerator, Tuple
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
                await self.memory_service.add_message(memory_key, "assistant", rag_result.answer)

            # 4. Log query
            processing_time_ms = (time.time() - start_time) * 1000
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

            # 5. Update metrics
            query_counter.labels(source=source.value).inc()
            query_duration.labels(source=source.value).observe(processing_time_ms / 1000)

            # 6. Return result
            return QueryResult(
                query_id=query_id,
                answer=rag_result.answer,
                sources=rag_result.sources,
                processing_time_ms=processing_time_ms,
                timestamp=datetime.utcnow(),
                context_used=rag_result.retrieved_docs,
            )

        except Exception as e:
            logger.error("Error processing query: {} (query_id: {})", e, query_id)
            raise

    async def process_query_stream(
        self,
        question: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        source: QuerySource = QuerySource.API,
        enable_memory: bool = True,
        enable_feedback: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[Tuple[str, str], None]:
        """
        Process a query through the RAG pipeline with streaming

        Args:
            question: User's question
            user_id: User identifier (for memory and analytics)
            session_id: Session identifier (overrides user_id for memory)
            source: Query source (telegram/api)
            enable_memory: Whether to use chat history
            enable_feedback: Whether to enable feedback tracking
            metadata: Additional metadata

        Yields:
            Tuples of (query_id, chunk) where first yield contains query_id,
            subsequent yields contain answer chunks
        """
        start_time = time.time()
        query_id = str(uuid.uuid4())

        logger.info(
            f"Processing streaming query from {source}",
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

            # 2. Run RAG pipeline steps manually for streaming
            # Step 0: Query expansion (if enabled)
            search_query = question
            if settings.QUERY_EXPANSION_ENABLED:
                search_query = await self.rag_pipeline.query_expander.expand_query(question)
                logger.info(f"Query expanded for streaming: '{question}' → '{search_query}'")

            # Step 1: Embedding
            query_embedding = await self.rag_pipeline.embedder.embed_query(search_query)

            # Step 2: Vector search
            retrieved_docs = await self.rag_pipeline.retriever.similarity_search(query_embedding)

            if not retrieved_docs:
                # Yield query_id first
                yield (query_id, "")
                # Yield the error message
                error_msg = (
                    "⚠️ База знаний еще не заполнена.\n\n"
                    "В настоящий момент таблица с векторными эмбеддингами пуста или еще не создана."
                )
                yield (query_id, error_msg)

                # Log query
                processing_time_ms = (time.time() - start_time) * 1000
                await self._log_query(
                    query_id=query_id,
                    question=question,
                    answer=error_msg,
                    user_id=user_id,
                    session_id=session_id,
                    source=source,
                    processing_time_ms=processing_time_ms,
                    enable_feedback=False,
                    metadata=metadata or {},
                )
                return

            # Step 3: Reranking
            top_source_paths = await self.rag_pipeline.reranker.extract_top_sources(
                question, retrieved_docs
            )

            if not top_source_paths:
                # Yield query_id first
                yield (query_id, "")
                # Yield the error message
                error_msg = (
                    "Для ответа необходимо уточнить или перефразировать вопрос, "
                    "а также добавить более подробное описание."
                )
                yield (query_id, error_msg)

                # Log query
                processing_time_ms = (time.time() - start_time) * 1000
                await self._log_query(
                    query_id=query_id,
                    question=question,
                    answer=error_msg,
                    user_id=user_id,
                    session_id=session_id,
                    source=source,
                    processing_time_ms=processing_time_ms,
                    enable_feedback=False,
                    metadata=metadata or {},
                )
                return

            # Step 4: Fetch full documents
            full_documents = await self.rag_pipeline.enhancer.fetch_full_documents(top_source_paths)

            # Step 5: Aggregate context
            context = self.rag_pipeline.enhancer.aggregate_context(full_documents)

            # Yield query_id as first item
            yield (query_id, "")

            # Step 6: Stream answer generation
            answer_chunks = []
            async for chunk in self.rag_pipeline.generator.generate_answer_stream(
                question=question,
                context=context,
                chat_history=chat_history,
            ):
                answer_chunks.append(chunk)
                yield (query_id, chunk)

            # Combine full answer
            full_answer = "".join(answer_chunks)

            # 3. Update chat history
            if enable_memory and (user_id or session_id):
                memory_key = session_id or user_id
                await self.memory_service.add_message(memory_key, "user", question)
                await self.memory_service.add_message(memory_key, "assistant", full_answer)

            # 4. Log query
            processing_time_ms = (time.time() - start_time) * 1000
            await self._log_query(
                query_id=query_id,
                question=question,
                answer=full_answer,
                user_id=user_id,
                session_id=session_id,
                source=source,
                processing_time_ms=processing_time_ms,
                enable_feedback=enable_feedback,
                metadata=metadata or {},
            )

            # 5. Update metrics
            query_counter.labels(source=source.value).inc()
            query_duration.labels(source=source.value).observe(processing_time_ms / 1000)

        except Exception as e:
            logger.error("Error processing streaming query: {} (query_id: {})", e, query_id)
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
