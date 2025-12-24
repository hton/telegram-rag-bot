"""Query API routes"""
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from src.api.schemas.query import QueryRequest, QueryResponse, FeedbackRequest
from src.api.dependencies import get_query_service, get_feedback_service
from src.services.query_service import QueryService
from src.services.feedback import FeedbackService
from src.schemas.enums import QuerySource
from src.core.config import settings

router = APIRouter()


def should_request_feedback(answer: str) -> bool:
    """
    Определяет, нужно ли предлагать feedback для ответа.
    Возвращает False если ответ пустой или система не нашла информацию.
    """
    no_feedback_phrases = [
        "Для ответа необходимо уточнить или перефразировать вопрос",
        "База знаний еще не заполнена",
    ]
    return not any(phrase in answer for phrase in no_feedback_phrases)


@router.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    query_service: QueryService = Depends(get_query_service),
) -> QueryResponse:
    """
    Process RAG query via API

    - **question**: User question
    - **user_id**: Optional user identifier for chat history
    - **session_id**: Optional session ID
    - **enable_memory**: Whether to include chat history
    - **enable_feedback**: Whether to include feedback tracking
    - **metadata**: Additional metadata (source, context, etc.)
    """
    try:
        logger.info(f"API query received: {request.question[:100]}...")

        result = await query_service.process_query(
            question=request.question,
            user_id=request.user_id,
            session_id=request.session_id,
            enable_memory=request.enable_memory,
            enable_feedback=request.enable_feedback,
            source=QuerySource.API,
            metadata=request.metadata or {},
        )

        # Build response
        # Определяем, нужно ли включать feedback
        can_feedback = request.enable_feedback and should_request_feedback(result.answer)

        response = QueryResponse(
            query_id=result.query_id,
            answer=result.answer,
            sources=result.sources,
            feedback_enabled=can_feedback,
            feedback_url=f"/api/v1/query/feedback/{result.query_id}" if can_feedback else None,
            processing_time_ms=result.processing_time_ms,
            timestamp=result.timestamp,
        )

        # Add debug info if enabled
        if settings.DEBUG:
            response.debug_info = {
                "context_used_length": len(result.context_used),
                "sources_count": len(result.sources),
            }

        return response

    except Exception as e:
        logger.error("Error processing query: {}", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/feedback/{query_id}")
async def submit_feedback(
    query_id: str,
    request: FeedbackRequest,
    feedback_service: FeedbackService = Depends(get_feedback_service),
):
    """Submit feedback for a specific query"""
    try:
        await feedback_service.save_feedback(
            query_id=query_id,
            rating=request.rating,
            comment=request.comment,
        )

        return {
            "status": "success",
            "message": "Feedback saved successfully",
            "query_id": query_id,
            "rating": request.rating,
        }

    except Exception as e:
        logger.error("Error saving feedback: {}", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
