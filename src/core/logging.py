"""Logging configuration using loguru"""
import sys
import zipfile
from pathlib import Path
from loguru import logger

from src.core.config import settings


def safe_compression(log_path: str) -> None:
    """
    Safely compress log file with error handling.

    Handles race conditions during log rotation where the file
    may already be renamed/compressed by loguru.

    Args:
        log_path: Path to the log file to compress
    """
    try:
        source_path = Path(log_path)

        # Check if file exists (may already be rotated)
        if not source_path.exists():
            return

        # Create zip archive
        zip_path = source_path.with_suffix(source_path.suffix + ".zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(source_path, source_path.name)

        # Remove original file after successful compression
        source_path.unlink()

    except FileNotFoundError:
        # File already processed - this is expected during rotation
        pass
    except Exception as e:
        # Log other errors but don't crash
        print(f"Warning: Failed to compress log {log_path}: {e}", file=sys.stderr)


def setup_logging() -> None:
    """Configure loguru logging"""

    # Remove default handler
    logger.remove()

    # Console handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.LOG_LEVEL,
        colorize=True,
    )

    # File handler
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logger.add(
        log_dir / "app_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="30 days",
        level=settings.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        compression=safe_compression,
    )

    # Error log
    logger.add(
        log_dir / "error_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="30 days",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        compression=safe_compression,
    )

    logger.info("Logging configured successfully")
