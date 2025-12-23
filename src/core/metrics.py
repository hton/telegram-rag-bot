"""Prometheus metrics definitions"""
from prometheus_client import Counter, Histogram, Gauge

# Query metrics
query_counter = Counter(
    "rag_queries_total",
    "Total number of RAG queries processed",
    ["source"],  # telegram or api
)

query_duration = Histogram(
    "rag_query_duration_seconds",
    "RAG query processing duration in seconds",
    ["source"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
)

query_errors = Counter(
    "rag_query_errors_total",
    "Total number of RAG query errors",
    ["source", "error_type"],
)

# Feedback metrics
feedback_counter = Counter(
    "rag_feedback_total",
    "Total number of feedback submissions",
    ["rating"],  # good, notbad, bad
)

# OpenAI API metrics
openai_api_calls = Counter(
    "openai_api_calls_total",
    "Total number of OpenAI API calls",
    ["model", "operation"],  # operation: embedding, completion
)

openai_api_duration = Histogram(
    "openai_api_duration_seconds",
    "OpenAI API call duration in seconds",
    ["model", "operation"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
)

openai_api_errors = Counter(
    "openai_api_errors_total",
    "Total number of OpenAI API errors",
    ["model", "operation", "error_type"],
)

openai_tokens_used = Counter(
    "openai_tokens_used_total",
    "Total number of tokens used",
    ["model", "token_type"],  # token_type: prompt, completion
)

# Vector search metrics
vector_search_duration = Histogram(
    "vector_search_duration_seconds",
    "Vector search duration in seconds",
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0],
)

vector_search_results = Histogram(
    "vector_search_results_count",
    "Number of results returned from vector search",
    buckets=[0, 5, 10, 15, 20, 50],
)

# Active sessions
active_users = Gauge(
    "rag_active_users",
    "Number of active users (with recent queries)",
)

active_sessions = Gauge(
    "rag_active_sessions",
    "Number of active chat sessions",
)
