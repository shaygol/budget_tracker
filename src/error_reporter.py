"""
Error reporting mechanism with context capture and error report generation.
"""
import logging
import traceback
import sys
import platform
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import json

logger = logging.getLogger(__name__)


class ErrorReporter:
    """Captures and reports errors with full context."""

    def __init__(self, error_dir: Path):
        """
        Initialize error reporter.

        Args:
            error_dir: Directory to save error reports
        """
        self.error_dir = Path(error_dir)
        self.error_dir.mkdir(parents=True, exist_ok=True)

    def capture_exception(self, exctype: type, value: Exception, tb,
                         context: Optional[Dict[str, Any]] = None) -> str:
        """
        Capture exception with full context and generate error report.

        Args:
            exctype: Exception type
            value: Exception instance
            tb: Traceback object
            context: Additional context dictionary

        Returns:
            Error report ID (filename without extension)
        """
        error_id = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        report_path = self.error_dir / f"error_{error_id}.json"

        # Get system information
        system_info = {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'python_version': sys.version,
            'architecture': platform.architecture()[0]
        }

        # Get stack trace
        stack_trace = ''.join(traceback.format_exception(exctype, value, tb))

        # Build error report
        report = {
            'error_id': error_id,
            'timestamp': datetime.now().isoformat(),
            'exception_type': exctype.__name__,
            'exception_message': str(value),
            'stack_trace': stack_trace,
            'system_info': system_info,
            'context': context or {}
        }

        # Save report
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.error(f"Error report saved: {report_path}")
        except Exception as e:
            logger.error(f"Failed to save error report: {e}")

        return error_id

    def generate_user_message(self, error_id: str, exception: Exception) -> str:
        """
        Generate user-friendly error message with error ID.

        Args:
            error_id: Error report ID
            exception: Exception instance

        Returns:
            User-friendly error message
        """
        return (
            f"An unexpected error occurred.\n\n"
            f"Error ID: {error_id}\n"
            f"Error: {str(exception)}\n\n"
            f"An error report has been saved. Please provide the Error ID if reporting this issue."
        )


def setup_error_reporting(error_dir: Optional[Path] = None) -> ErrorReporter:
    """
    Set up global error reporting.

    Args:
        error_dir: Directory for error reports (defaults to output/errors)

    Returns:
        ErrorReporter instance
    """
    if error_dir is None:
        from src.config import OUTPUT_DIR
        error_dir = OUTPUT_DIR / 'errors'

    reporter = ErrorReporter(error_dir)

    def exception_hook(exctype, value, tb):
        """Global exception handler."""
        error_id = reporter.capture_exception(exctype, value, tb)
        logger.critical(f"Unhandled exception (ID: {error_id}): {value}", exc_info=(exctype, value, tb))

        # Also log to console
        print(f"\nFatal Error (ID: {error_id}):")
        traceback.print_exception(exctype, value, tb)

    sys.excepthook = exception_hook

    return reporter

