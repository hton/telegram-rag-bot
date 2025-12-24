"""Application configuration"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # OpenAI Configuration
    OPENAI_API_KEY: str
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    EMBEDDING_DIMENSIONS: int = 1536
    LLM_MODEL: str = "gpt-4o-mini"
    TEMPERATURE: float = 0.0
    MAX_TOKENS: int = 1000

    # PostgreSQL Configuration
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "pgdb"
    DB_USER: str = "pguser"
    DB_PASSWORD: str = "1q2w3e4r"

    # Vector Table Configuration
    VECTOR_TABLE: str = "openai_221225"

    # RAG Configuration
    CONTEXT_WINDOW: int = 3
    TOP_K_RESULTS: int = 15
    RERANK_TOP_K: int = 5
    QUERY_EXPANSION_ENABLED: bool = True  # Enable query expansion for better recall with abbreviations and technical terms

    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN: str = ""
    BOT_USERNAME: str = "isplabtg_bot"
    WEBHOOK_ENABLED: bool = False
    WEBHOOK_URL: Optional[str] = None
    WEBHOOK_PATH: str = "/webhook/telegram"
    TELEGRAM_ENABLE_FEEDBACK: bool = True

    # Security Configuration
    RATE_LIMIT_ENABLED: bool = True  # Enable rate limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 5  # Max requests per minute per user
    RATE_LIMIT_REQUESTS_PER_HOUR: int = 20  # Max requests per hour per user

    # Whitelist Configuration (empty = all allowed)
    WHITELIST_USERS_ENABLED: bool = False  # Enable user whitelist for private chats
    WHITELIST_USERS: str = ""  # Comma-separated user IDs, e.g., "123456789,987654321"
    WHITELIST_GROUPS_ENABLED: bool = False  # Enable group whitelist
    WHITELIST_GROUPS: str = ""  # Comma-separated group/chat IDs, e.g., "-1001234567890,-1009876543210"

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8080
    API_ENABLE_FEEDBACK_BY_DEFAULT: bool = False
    API_REQUIRE_AUTH: bool = False
    API_KEY: Optional[str] = None

    # Application
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Metrics
    METRICS_ENABLED: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        """Get async database URL"""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def database_url_sync(self) -> str:
        """Get sync database URL (for alembic)"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings()
