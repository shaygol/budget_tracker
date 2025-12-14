"""
Structured logging with rotation support.
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional, Any
from src.config import get_log_level

# Default log rotation settings
MAX_LOG_SIZE_MB = 10
BACKUP_COUNT = 5


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter for structured logging with key-value pairs.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with structured key-value pairs.

        Args:
            record: Log record to format

        Returns:
            Formatted log message string
        """
        # Base format with timestamp and level
        base_msg = super().format(record)

        # Extract structured data from extra fields
        structured_data = {}
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                          'levelname', 'levelno', 'lineno', 'module', 'msecs', 'message',
                          'pathname', 'process', 'processName', 'relativeCreated', 'thread',
                          'threadName', 'exc_info', 'exc_text', 'stack_info']:
                structured_data[key] = value

        # Add structured data to message if present
        if structured_data:
            kv_pairs = ' '.join(f"{k}={v}" for k, v in structured_data.items())
            return f"{base_msg} {kv_pairs}"

        return base_msg


def setup_logging(log_dir: str, log_file_name: str,
                  max_bytes_mb: Optional[int] = None,
                  backup_count: Optional[int] = None,
                  log_level: Optional[int] = None) -> None:
    """
    Set up logging with structured formatting and rotation.

    Args:
        log_dir: Directory for log files
        log_file_name: Name of the log file
        max_bytes_mb: Maximum log file size in MB before rotation (uses settings if None)
        backup_count: Number of backup log files to keep (uses settings if None)
        log_level: Log level constant (uses settings if None)
    """
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, log_file_name)

    # Use parameters if provided, otherwise use defaults
    if max_bytes_mb is None:
        max_bytes_mb = MAX_LOG_SIZE_MB
    if backup_count is None:
        backup_count = BACKUP_COUNT
    if log_level is None:
        # Get from settings.json or use config.py default
        log_level = get_log_level()

    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Structured formatter
    formatter = StructuredFormatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Clear existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()

    # Rotating file handler
    max_bytes = max_bytes_mb * 1024 * 1024  # Convert MB to bytes
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler (non-rotating)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.debug("Logging initialized", extra={
        'log_file': log_file,
        'max_size_mb': max_bytes_mb,
        'backup_count': backup_count
    })


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_operation(operation: str, logger: Optional[logging.Logger] = None, **kwargs: Any) -> None:
    """
    Log a structured operation with key-value pairs.

    Args:
        operation: Operation name/description
        logger: Logger instance (uses root logger if None)
        **kwargs: Additional key-value pairs to include in log
    """
    if logger is None:
        logger = logging.getLogger()

    # Create extra dict for structured logging
    extra = {'operation': operation, **kwargs}
    logger.info(operation, extra=extra)