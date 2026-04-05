from __future__ import annotations

import logging
from pathlib import Path

from utils.paths import LOGS_DIR

LOG_FILE = LOGS_DIR / "app.log"


class LogService:
    _initialized = False

    @classmethod
    def ensure_logging(cls) -> None:
        if cls._initialized:
            return

        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
            handlers=[
                logging.FileHandler(LOG_FILE, encoding="utf-8"),
            ],
        )
        cls._initialized = True

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        cls.ensure_logging()
        return logging.getLogger(name)

    @classmethod
    def get_log_file(cls) -> Path:
        cls.ensure_logging()
        return Path(LOG_FILE)
