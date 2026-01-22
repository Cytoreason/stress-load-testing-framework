"""
Logging utility for the load testing framework.

Provides colored console output and optional file logging.
"""
import logging
from pathlib import Path
from typing import Optional

import colorlog

__all__ = ["setup_logger", "get_logger"]

# Module-level logger cache to prevent duplicates
_loggers: dict[str, logging.Logger] = {}


def setup_logger(
    name: str = "LoadTest",
    log_level: str = "INFO",
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Set up a colored logger for the load testing framework.

    Uses a cache to prevent creating duplicate loggers with the same name.

    Args:
        name: Logger name (used as identifier)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to write logs to

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logger("MyTest", "DEBUG")
        >>> logger.info("Test started")
    """
    # Return cached logger if exists
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Clear any existing handlers to prevent duplicates
    logger.handlers.clear()

    # Console handler with colors
    console_handler = colorlog.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    console_format = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s%(reset)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )

    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler if log file is specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)

        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    # Cache the logger
    _loggers[name] = logger

    return logger


def get_logger(name: str = "LoadTest") -> logging.Logger:
    """
    Get an existing logger or create a new one with defaults.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    if name in _loggers:
        return _loggers[name]
    return setup_logger(name)
