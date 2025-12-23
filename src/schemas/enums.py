"""Enum definitions for the application"""
from enum import Enum


class QuerySource(str, Enum):
    """Source of the query"""
    TELEGRAM = "telegram"
    API = "api"


class FeedbackType(str, Enum):
    """Feedback types"""
    GOOD = "good"
    NOTBAD = "notbad"
    BAD = "bad"
