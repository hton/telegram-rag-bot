"""FastAPI application setup"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
from loguru import logger

from src.core.config import settings
from src.core.database import init_db, close_db
from src.core.logging import setup_logging
from src.api.routes import query, health, admin, metrics as metrics_route
from src.api.middleware import APIKeyMiddleware, IPWhitelistMiddleware, APIRateLimitMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    setup_logging()
    logger.info("Starting FastAPI application...")
    await init_db()
    logger.info("Database initialized")

    yield

    # Shutdown
    logger.info("Shutting down FastAPI application...")
    await close_db()
    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Telegram RAG Bot API",
    description="API for RAG-powered Telegram bot",
    version="0.1.0",
    lifespan=lifespan,
)

# Add security middleware (order matters!)
# 1. IP Whitelist (block unauthorized IPs first)
app.add_middleware(IPWhitelistMiddleware)

# 2. Rate Limiting (prevent spam from allowed IPs)
app.add_middleware(APIRateLimitMiddleware)

# 3. API Key Authentication (verify API key)
app.add_middleware(APIKeyMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Prometheus metrics
if settings.METRICS_ENABLED:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(query.router, prefix="/api/v1", tags=["Query"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(metrics_route.router, prefix="/api/v1", tags=["Metrics"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Telegram RAG Bot API",
        "version": "0.1.0",
        "status": "running",
    }
