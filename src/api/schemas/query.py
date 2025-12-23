"""Query API schemas"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class QueryRequest(BaseModel):
    """API query request schema"""
    question: str = Field(..., min_length=1, max_length=1000, description="User question")
    user_id: Optional[str] = Field(None, description="User identifier for chat history")
    session_id: Optional[str] = Field(None, description="Session identifier")
    enable_memory: bool = Field(True, description="Enable chat history")
    enable_feedback: bool = Field(False, description="Return feedback tracking info")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class QueryResponse(BaseModel):
    """API query response schema"""
    query_id: str
    answer: str
    sources: List[str]

    # Optional fields based on enable_feedback
    feedback_enabled: bool = False
    feedback_url: Optional[str] = None

    # Metadata
    processing_time_ms: float
    timestamp: datetime

    # Debug info (only if DEBUG=true)
    debug_info: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class FeedbackRequest(BaseModel):
    """Feedback submission schema"""
    rating: str = Field(..., pattern="^(good|notbad|bad)$", description="Rating value")
    comment: Optional[str] = Field(None, max_length=500, description="Optional comment")
