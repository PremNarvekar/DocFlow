import logging
import json
import traceback
from typing import Any

def get_structured_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = JSONFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add explicit structured fields attached via 'extra'
        if hasattr(record, "structured_data"):
            for k, v in getattr(record, "structured_data").items():
                if k not in log_record:  # don't override base fields
                    log_record[k] = v

        if record.exc_info:
            log_record["exception"] = traceback.format_exception(*record.exc_info)

        return json.dumps(log_record)
