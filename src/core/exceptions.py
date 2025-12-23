"""Custom exceptions for the application"""


class ApplicationError(Exception):
    """Base exception for all application errors"""
    pass


class EmbeddingError(ApplicationError):
    """Error during embedding generation"""
    pass


class RetrievalError(ApplicationError):
    """Error during document retrieval"""
    pass


class RerankingError(ApplicationError):
    """Error during reranking"""
    pass


class GenerationError(ApplicationError):
    """Error during answer generation"""
    pass


class RAGPipelineError(ApplicationError):
    """Error in RAG pipeline execution"""
    pass


class DatabaseError(ApplicationError):
    """Database operation error"""
    pass


class ConfigurationError(ApplicationError):
    """Configuration error"""
    pass
