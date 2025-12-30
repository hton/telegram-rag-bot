"""Cost calculation utility for OpenAI API usage"""
from typing import Dict


class CostCalculator:
    """Calculate costs for OpenAI API usage based on token consumption"""

    # Pricing from docs/COST_ANALYSIS.md (as of December 2025)
    PRICING = {
        "gpt-4o-mini": {
            "input": 0.15 / 1_000_000,  # $0.15 per 1M tokens
            "output": 0.60 / 1_000_000,  # $0.60 per 1M tokens
        },
        "text-embedding-ada-002": {
            "input": 0.10 / 1_000_000,  # $0.10 per 1M tokens
        },
    }

    # Exchange rate from COST_ANALYSIS.md (December 2025)
    USD_TO_RUB = 78.0

    @staticmethod
    def calculate_cost(tokens_data: Dict[str, Dict[str, int]]) -> Dict[str, float]:
        """
        Calculate total cost from token usage across all RAG pipeline steps.

        Args:
            tokens_data: Dictionary with token usage per operation:
                {
                    "embedding": {"input": 30},
                    "query_expansion": {"input": 200, "output": 100},
                    "reranking": {"input": 1000, "output": 150},
                    "generation": {"input": 2500, "output": 500}
                }

        Returns:
            Dictionary with costs in USD and RUB:
                {"usd": 0.0012, "rub": 0.094}
        """
        total_usd = 0.0

        # Embedding cost (text-embedding-ada-002)
        embedding_tokens = tokens_data.get("embedding", {}).get("input", 0)
        total_usd += embedding_tokens * CostCalculator.PRICING["text-embedding-ada-002"]["input"]

        # Query expansion cost (gpt-4o-mini)
        qe_input = tokens_data.get("query_expansion", {}).get("input", 0)
        qe_output = tokens_data.get("query_expansion", {}).get("output", 0)
        total_usd += qe_input * CostCalculator.PRICING["gpt-4o-mini"]["input"]
        total_usd += qe_output * CostCalculator.PRICING["gpt-4o-mini"]["output"]

        # Reranking cost (gpt-4o-mini)
        rerank_input = tokens_data.get("reranking", {}).get("input", 0)
        rerank_output = tokens_data.get("reranking", {}).get("output", 0)
        total_usd += rerank_input * CostCalculator.PRICING["gpt-4o-mini"]["input"]
        total_usd += rerank_output * CostCalculator.PRICING["gpt-4o-mini"]["output"]

        # Generation cost (gpt-4o-mini)
        gen_input = tokens_data.get("generation", {}).get("input", 0)
        gen_output = tokens_data.get("generation", {}).get("output", 0)
        total_usd += gen_input * CostCalculator.PRICING["gpt-4o-mini"]["input"]
        total_usd += gen_output * CostCalculator.PRICING["gpt-4o-mini"]["output"]

        # Convert to RUB
        total_rub = total_usd * CostCalculator.USD_TO_RUB

        return {
            "usd": round(total_usd, 6),
            "rub": round(total_rub, 4),
        }
