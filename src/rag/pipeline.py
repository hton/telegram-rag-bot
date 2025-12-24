"""
Main RAG Pipeline Orchestrator

This class coordinates all RAG components to process queries.
Matches the n8n workflow logic.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import time

from src.rag.embedder import OpenAIEmbedder
from src.rag.retriever import VectorRetriever
from src.rag.reranker import LLMReranker
from src.rag.retrieval_enhancer import RetrievalEnhancer
from src.rag.generator import AnswerGenerator
from src.rag.query_expander import QueryExpander
from src.core.exceptions import RAGPipelineError
from src.core.config import settings


@dataclass
class RAGResult:
    """Result from RAG pipeline execution"""
    answer: str
    sources: List[str]
    retrieved_docs: List[Dict[str, Any]]
    reranked_sources: List[str]
    context_used: str


class RAGPipeline:
    """
    Main RAG Pipeline

    Workflow:
    1. [Optional] Query expansion (expand with synonyms and terms)
    2. Embed query (OpenAI text-embedding-ada-002)
    3. Vector similarity search (pgvector, top 15)
    4. LLM reranking (GPT-4o-mini, select top 5 source_path)
    5. Fetch full documents for selected sources
    6. Generate answer with context (GPT-4o-mini)
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.query_expander = QueryExpander()
        self.embedder = OpenAIEmbedder()
        self.retriever = VectorRetriever(db)
        self.reranker = LLMReranker()
        self.enhancer = RetrievalEnhancer(db)
        self.generator = AnswerGenerator()

    async def run(
        self,
        question: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> RAGResult:
        """
        Execute full RAG pipeline

        Args:
            question: User's question
            chat_history: Optional chat history for context

        Returns:
            RAGResult with answer and metadata

        Raises:
            RAGPipelineError: If pipeline execution fails
        """
        try:
            pipeline_start = time.time()
            logger.info(f"Starting RAG pipeline for question: {question[:100]}...")

            # Step 0: Query expansion (if enabled)
            search_query = question
            if settings.QUERY_EXPANSION_ENABLED:
                step_start = time.time()
                logger.debug("Step 0: Expanding query")
                search_query = await self.query_expander.expand_query(question)
                step_time = (time.time() - step_start) * 1000
                logger.info(f"⏱️ Step 0 (Query Expansion): {step_time:.0f}ms")

            # Step 1: Generate query embedding
            step_start = time.time()
            logger.debug("Step 1: Generating query embedding")
            query_embedding = await self.embedder.embed_query(search_query)
            step_time = (time.time() - step_start) * 1000
            logger.info(f"⏱️ Step 1 (Embedding): {step_time:.0f}ms")

            # Step 2: Vector similarity search (top 15 results)
            step_start = time.time()
            logger.debug("Step 2: Performing vector similarity search")
            retrieved_docs = await self.retriever.similarity_search(
                query_embedding=query_embedding,
            )
            step_time = (time.time() - step_start) * 1000
            logger.info(f"⏱️ Step 2 (Vector Search): {step_time:.0f}ms")

            if not retrieved_docs:
                logger.warning("No documents found in vector search - knowledge base may be empty")
                return RAGResult(
                    answer=(
                        "⚠️ База знаний еще не заполнена.\n\n"
                        "В настоящий момент таблица с векторными эмбеддингами пуста или еще не создана. "
                        "Для работы системы необходимо загрузить данные через сервис индексации документов.\n\n"
                        "Пожалуйста, обратитесь к администратору для заполнения базы знаний."
                    ),
                    sources=[],
                    retrieved_docs=[],
                    reranked_sources=[],
                    context_used="",
                )

            logger.info(f"Retrieved {len(retrieved_docs)} documents from vector search")

            # Step 3: LLM-based reranking (select top 5 source_path)
            step_start = time.time()
            logger.debug("Step 3: Reranking documents with LLM")
            top_source_paths = await self.reranker.extract_top_sources(
                question=question,
                documents=retrieved_docs,
            )
            step_time = (time.time() - step_start) * 1000
            logger.info(f"⏱️ Step 3 (Reranking): {step_time:.0f}ms")

            if not top_source_paths:
                logger.warning("No sources selected after reranking")
                return RAGResult(
                    answer="Для ответа необходимо уточнить или перефразировать вопрос, а также добавить более подробное описание.",
                    sources=[],
                    retrieved_docs=retrieved_docs,
                    reranked_sources=[],
                    context_used="",
                )

            logger.info(f"Reranked to {len(top_source_paths)} top sources: {top_source_paths}")

            # Step 4: Fetch full document context for selected sources
            step_start = time.time()
            logger.debug("Step 4: Fetching full documents for top sources")
            full_documents = await self.enhancer.fetch_full_documents(
                source_paths=top_source_paths,
            )
            step_time = (time.time() - step_start) * 1000
            logger.info(f"⏱️ Step 4 (Fetch Documents): {step_time:.0f}ms")

            # Step 5: Aggregate context
            step_start = time.time()
            logger.debug("Step 5: Aggregating context from documents")
            context = self.enhancer.aggregate_context(full_documents)
            step_time = (time.time() - step_start) * 1000
            logger.info(f"⏱️ Step 5 (Aggregate Context): {step_time:.0f}ms")

            # Step 6: Generate answer
            step_start = time.time()
            logger.debug("Step 6: Generating final answer")
            answer = await self.generator.generate_answer(
                question=question,
                context=context,
                chat_history=chat_history,
            )
            step_time = (time.time() - step_start) * 1000
            logger.info(f"⏱️ Step 6 (Generate Answer): {step_time:.0f}ms")

            pipeline_time = (time.time() - pipeline_start) * 1000
            logger.info(f"✅ RAG pipeline completed in {pipeline_time:.0f}ms")

            return RAGResult(
                answer=answer,
                sources=top_source_paths,
                retrieved_docs=retrieved_docs,
                reranked_sources=top_source_paths,
                context_used=context,
            )

        except Exception as e:
            logger.error("RAG pipeline failed: {}", e, exc_info=True)
            raise RAGPipelineError(f"RAG pipeline execution failed: {e}")

    async def run_with_debug(
        self,
        question: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Execute RAG pipeline with detailed debug information

        Useful for development and debugging
        """
        result = await self.run(question, chat_history)

        return {
            "answer": result.answer,
            "sources": result.sources,
            "debug": {
                "retrieved_docs_count": len(result.retrieved_docs),
                "retrieved_docs": result.retrieved_docs[:5],  # First 5 for brevity
                "reranked_sources": result.reranked_sources,
                "context_length": len(result.context_used),
                "context_preview": result.context_used[:500] + "...",
            }
        }
