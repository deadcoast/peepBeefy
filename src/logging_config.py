"""Logging configuration for peepBeefy.

This module sets up Python logging with file handlers, rotation, and
configurable log levels for debugging and diagnostics.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional


# Log directory and file paths
LOG_DIR = Path.home() / ".peepbeefy" / ".logs"
LOG_FILE = LOG_DIR / "peepbeefy.log"

# Log rotation settings
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 3  # Keep last 3 rotated files

# Default log level
DEFAULT_LOG_LEVEL = logging.INFO


def setup_logging(debug: bool = False) -> None:
    """Set up Python logging with file handler and rotation.
    
    Creates the .logs directory if it doesn't exist, configures log format
    with timestamp, level, module, and message, and sets up log file rotation.
    
    Args:
        debug: If True, set log level to DEBUG for verbose logging
    """
    # Create log directory if it doesn't exist
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        # If we can't create the log directory, fall back to console-only logging
        print(f"Warning: Failed to create log directory: {e}")
        _setup_console_only_logging(debug)
        return
    
    # Determine log level
    log_level = logging.DEBUG if debug else DEFAULT_LOG_LEVEL
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove any existing handlers
    root_logger.handlers.clear()
    
    # Create rotating file handler
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            LOG_FILE,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        
        # Create formatter with timestamp, level, module, and message
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to root logger
        root_logger.addHandler(file_handler)
        
        # Log startup message
        root_logger.info("=" * 60)
        root_logger.info(f"peepBeefy logging initialized (level: {logging.getLevelName(log_level)})")
        root_logger.info(f"Log file: {LOG_FILE}")
        root_logger.info("=" * 60)
        
    except OSError as e:
        # If we can't create the log file, fall back to console-only logging
        print(f"Warning: Failed to create log file: {e}")
        _setup_console_only_logging(debug)


def _setup_console_only_logging(debug: bool = False) -> None:
    """Set up console-only logging as fallback.
    
    Used when file logging cannot be initialized due to permission issues
    or other errors.
    
    Args:
        debug: If True, set log level to DEBUG for verbose logging
    """
    log_level = logging.DEBUG if debug else DEFAULT_LOG_LEVEL
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove any existing handlers
    root_logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(levelname)s - %(name)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    
    root_logger.warning("File logging unavailable, using console-only logging")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module.
    
    Args:
        name: Name of the module (typically __name__)
    
    Returns:
        Logger instance configured with the application settings
    """
    return logging.getLogger(name)


def check_and_rotate_logs() -> None:
    """Check log file size at startup and rotate if needed.
    
    This function is called at application startup to ensure log files
    don't grow unbounded. The RotatingFileHandler will handle rotation
    automatically during runtime, but this provides an explicit check
    at startup.
    """
    if not LOG_FILE.exists():
        return
    
    try:
        file_size = LOG_FILE.stat().st_size
        
        if file_size > MAX_LOG_SIZE:
            logger = logging.getLogger(__name__)
            logger.info(f"Log file size ({file_size} bytes) exceeds limit ({MAX_LOG_SIZE} bytes), rotating...")
            
            # Force rotation by creating a new handler
            # The RotatingFileHandler will handle the rotation automatically
            for handler in logging.getLogger().handlers:
                if isinstance(handler, logging.handlers.RotatingFileHandler):
                    handler.doRollover()
                    logger.info("Log rotation complete")
                    break
    except Exception as e:
        # Don't fail if rotation check fails
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to check/rotate logs: {e}")
