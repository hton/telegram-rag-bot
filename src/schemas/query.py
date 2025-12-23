"""Query-related schemas"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel

from src.schemas.enums import QuerySource


class QueryContext(BaseModel):
    """Unified query context"""
    question: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    source: QuerySource
    enable_memory: bool = True
    enable_feedback: bool = True
    metadata: Dict[str, Any] = {}


class QueryResult(BaseModel):
    """Unified query result"""
    query_id: str
    answer: str
    sources: List[str]
    processing_time_ms: float
    timestamp: datetime
    context_used: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True
