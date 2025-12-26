"""Logging configuration with structured logging."""
import logging
import sys
import json
from typing import Any, Dict
from bot.config import settings


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON or plain text."""
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, "extra_data") and record.extra_data:
            log_data.update(record.extra_data)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        if settings.log_format == "json":
            return json.dumps(log_data, ensure_ascii=False)
        else:
            # Plain text format
            msg = record.getMessage()
            if hasattr(record, "extra_data") and record.extra_data:
                # Pretty print extra data
                params_list = []
                for k, v in record.extra_data.items():
                    # Truncate long values
                    v_str = str(v)
                    if len(v_str) > 500:
                        v_str = v_str[:500] + "... (truncated)"
                    params_list.append(f"{k}={v_str}")
                params = ", ".join(params_list)
                msg = f"{msg} | {params}"
            return f"[{record.levelname}] {msg}"


class StructuredLogger:
    """Wrapper for structured logging."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        
    def _log(self, level: int, event: str, **kwargs):
        """Internal log method with structured data."""
        # Create log record with extra data
        record = self.logger.makeRecord(
            self.logger.name,
            level,
            "(unknown file)",
            0,
            event,
            (),
            None,
            func=None
        )
        record.extra_data = kwargs if kwargs else {}
        self.logger.handle(record)
    
    def debug(self, event: str, **kwargs):
        """Log debug message."""
        self._log(logging.DEBUG, event, **kwargs)
    
    def info(self, event: str, **kwargs):
        """Log info message."""
        self._log(logging.INFO, event, **kwargs)
    
    def warning(self, event: str, **kwargs):
        """Log warning message."""
        self._log(logging.WARNING, event, **kwargs)
    
    def error(self, event: str, **kwargs):
        """Log error message."""
        self._log(logging.ERROR, event, **kwargs)
    
    def critical(self, event: str, **kwargs):
        """Log critical message."""
        self._log(logging.CRITICAL, event, **kwargs)


# Configure root logger
def setup_logging():
    """Setup logging configuration."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    
    # Set formatter
    formatter = StructuredFormatter()
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    
    # Suppress noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)


# Initialize logging
setup_logging()

# Create default logger
logger = StructuredLogger("bot")
