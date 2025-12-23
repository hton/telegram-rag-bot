"""CLI commands for the application"""
import asyncio
import sys
from typing import Optional

import typer
import uvicorn
from loguru import logger

from src.core.config import settings
from src.core.logging import setup_logging
from src.core.database import init_db, close_db
from src.bot.bot import create_bot, get_dispatcher

app = typer.Typer(help="Telegram RAG Bot CLI")


@app.command()
def run_bot(
    polling: bool = typer.Option(True, help="Use polling mode instead of webhook"),
):
    """Run Telegram bot"""
    setup_logging()
    logger.info("Starting Telegram bot...")

    async def start_bot():
        bot = create_bot()
        dp = get_dispatcher()

        try:
            # Initialize database
            await init_db()

            if polling:
                logger.info("Starting bot in polling mode...")
                await dp.start_polling(bot)
            else:
                # Webhook mode would be configured here
                logger.error("Webhook mode not implemented in CLI. Use run-api instead.")
                sys.exit(1)

        finally:
            await bot.session.close()
            await close_db()

    asyncio.run(start_bot())


@app.command()
def run_api(
    host: str = typer.Option(settings.API_HOST, help="API host"),
    port: int = typer.Option(settings.API_PORT, help="API port"),
    reload: bool = typer.Option(False, help="Enable auto-reload"),
):
    """Run FastAPI server"""
    setup_logging()
    logger.info(f"Starting FastAPI server on {host}:{port}...")

    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=settings.LOG_LEVEL.lower(),
    )


@app.command()
def migrate(
    message: Optional[str] = typer.Option(None, help="Migration message"),
    autogenerate: bool = typer.Option(True, help="Auto-generate migration"),
):
    """Create database migration"""
    import subprocess

    if message:
        cmd = ["alembic", "revision"]
        if autogenerate:
            cmd.append("--autogenerate")
        cmd.extend(["-m", message])

        logger.info(f"Creating migration: {message}")
        subprocess.run(cmd)
    else:
        logger.error("Migration message is required. Use --message")
        sys.exit(1)


@app.command()
def migrate_up(
    revision: str = typer.Argument("head", help="Target revision"),
):
    """Apply database migrations"""
    import subprocess

    logger.info(f"Applying migrations to {revision}...")
    subprocess.run(["alembic", "upgrade", revision])


@app.command()
def migrate_down(
    revision: str = typer.Argument("previous", help="Target revision ('previous' for -1, or specific revision)"),
):
    """Rollback database migrations"""
    import subprocess

    # Convert "previous" to "-1" for alembic
    if revision == "previous":
        revision = "-1"

    logger.info(f"Rolling back to {revision}...")
    subprocess.run(["alembic", "downgrade", revision])


@app.command()
def test_rag(
    question: str = typer.Argument(..., help="Question to test"),
):
    """Test RAG pipeline with a question"""
    setup_logging()

    async def test():
        from src.core.database import AsyncSessionLocal
        from src.rag.pipeline import RAGPipeline

        logger.info(f"Testing RAG pipeline with question: {question}")

        async with AsyncSessionLocal() as db:
            pipeline = RAGPipeline(db)

            result = await pipeline.run_with_debug(question)

            logger.info("=== RAG Pipeline Result ===")
            logger.info(f"Answer: {result['answer']}")
            logger.info(f"Sources: {result['sources']}")
            logger.info(f"Debug: {result['debug']}")

            print("\n=== ANSWER ===")
            print(result['answer'])
            print("\n=== SOURCES ===")
            for source in result['sources']:
                print(f"- {source}")

    asyncio.run(test())


@app.command()
def init():
    """Initialize database tables"""
    setup_logging()

    async def initialize():
        logger.info("Initializing database...")
        await init_db()
        logger.info("Database initialized successfully!")

    asyncio.run(initialize())


if __name__ == "__main__":
    app()
