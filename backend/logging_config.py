"""
NeXifyAI — Zentrales Logging-System
Einheitliches Logging auf allen Ebenen: JSON-Strukturiert, Log-Level pro Environment.
"""
import os
import sys
import json
import logging
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Production-taugliches JSON-Log-Format."""
    def format(self, record):
        log_entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data
        return json.dumps(log_entry, ensure_ascii=False, default=str)


def setup_logging():
    """Initialisiert das Logging-System basierend auf Environment."""
    env = os.environ.get("ENVIRONMENT", "development")
    is_prod = env in ("production", "prod", "staging")
    level = logging.INFO if is_prod else logging.DEBUG

    root = logging.getLogger()
    root.setLevel(level)

    # Entferne bestehende Handler
    for h in root.handlers[:]:
        root.removeHandler(h)

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)

    if is_prod:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))

    root.addHandler(handler)

    # Externe Libraries auf WARNING setzen
    for noisy in ["urllib3", "httpcore", "httpx", "asyncio", "uvicorn.access"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger("nexifyai").setLevel(level)

    return logging.getLogger("nexifyai")
