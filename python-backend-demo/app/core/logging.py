"""Logging configuration"""

import sys
from loguru import logger
from app.config import settings


def setup_logging() -> None:
    """Configure application logging"""
    # Remove default handler
    logger.remove()

    # Add console handler with colors
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG" if settings.DEBUG else "INFO",
        colorize=True,
    )

    # Add file handler for errors
    logger.add(
        "logs/error.log",
        rotation="100 MB",
        retention="10 days",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
    )

    logger.info(f"Logging configured - Level: {'DEBUG' if settings.DEBUG else 'INFO'}")
