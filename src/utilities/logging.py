"""Structured application logging for Studio-AI."""

import logging
import sys
from pathlib import Path
from typing import Optional

_initialized = False


def setup_logging(log_file: Optional[Path] = None, level: int = logging.INFO) -> logging.Logger:
    """Set up structured logging to file and console."""
    global _initialized
    logger = logging.getLogger("studio_ai")

    if _initialized:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(filename)s:%(lineno)d] - %(message)s"
    )

    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File Handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    _initialized = True
    return logger


def get_logger() -> logging.Logger:
    """Get studio_ai application logger instance."""
    return logging.getLogger("studio_ai")
