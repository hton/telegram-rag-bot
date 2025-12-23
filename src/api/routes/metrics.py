"""Metrics API routes"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/metrics/info")
async def metrics_info():
    """
    Information about available metrics

    Prometheus metrics are available at /metrics endpoint
    """
    return {
        "prometheus_endpoint": "/metrics",
        "available_metrics": {
            "counters": [
                "rag_queries_total",
                "rag_query_errors_total",
                "rag_feedback_total",
                "openai_api_calls_total",
                "openai_api_errors_total",
                "openai_tokens_used_total",
            ],
            "histograms": [
                "rag_query_duration_seconds",
                "openai_api_duration_seconds",
                "vector_search_duration_seconds",
                "vector_search_results_count",
            ],
            "gauges": [
                "rag_active_users",
                "rag_active_sessions",
            ],
        },
    }
