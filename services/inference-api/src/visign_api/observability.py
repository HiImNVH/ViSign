# services/inference-api/src/visign_api/observability.py
# Log JSON co cau truc, chi ghi field van hanh duoc phep va khong bao gio ghi payload (T023).
import json
import logging
import sys
from typing import Any

LOGGER_NAME = "visign_api"

# Danh sach trang: field ngoai danh sach (clip, frame, landmark, ten file...) bi bo qua
ALLOWED_CONTEXT_KEYS = (
    "requestId",
    "modelVersion",
    "processingTimeMs",
    "timingsMs",
    "accepted",
    "errorCode",
    "method",
    "path",
    "statusCode",
)

# Ten muc log theo .agent/core.md muc 5.1
CORE_LEVEL_NAMES = {
    logging.DEBUG: "DEBUG",
    logging.INFO: "INFO",
    logging.WARNING: "WARN",
    logging.ERROR: "ERROR",
    logging.CRITICAL: "ERROR",
}


class StructuredJsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_line: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": CORE_LEVEL_NAMES.get(record.levelno, "INFO"),
            "logger": record.name,
            "message": record.getMessage(),
        }
        log_line.update(extract_allowed_context(record))
        if record.exc_info:
            log_line["exception"] = self.formatException(record.exc_info)
        # ensure_ascii giu dong log khi stdout Windows bi chuyen huong bang code page cu
        return json.dumps(log_line, ensure_ascii=True, default=str)


def extract_allowed_context(record: logging.LogRecord) -> dict[str, Any]:
    return {
        context_key: getattr(record, context_key)
        for context_key in ALLOWED_CONTEXT_KEYS
        if hasattr(record, context_key)
    }


def configure_logging() -> logging.Logger:
    service_logger = logging.getLogger(LOGGER_NAME)
    service_logger.setLevel(logging.INFO)
    # Goi lai khi reload app hoac trong test khong duoc gan them handler
    if not service_logger.handlers:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(StructuredJsonFormatter())
        service_logger.addHandler(stdout_handler)
    service_logger.propagate = False
    return service_logger
