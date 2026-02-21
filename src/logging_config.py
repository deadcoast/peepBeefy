"""
Logging configuration for peepBeefy.

This module sets up centralized logging with file handlers, rotation,
and configurable log levels.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional


# Log directory and file paths
LOG_DIR = Path(".logs")
LOG_FILE = LOG_DIR / "peepbeefy.log"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 3  # Keep last 3 rotated files


def setup_logging(debug: bool = False) -> None:
    """
    Configure logging for peepBeefy application.
    
    Args:
        debug: If True, set log level to DEBUG; otherwise INFO
    """
    # Create .logs directory if it doesn't exist
    LOG_DIR.mkdir(exist_ok=True)
    
    # Determine log level
    log_level = logging.DEBUG if debug else logging.INFO
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove any existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Create file handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    
    # Create formatter with timestamp, level, module, and message
    formatter = logging.Formatter(
        fmt='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    # Add handler to root logger
    root_logger.addHandler(file_handler)
    
    # Log initialization
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized (level={'DEBUG' if debug else 'INFO'})")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Module name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
