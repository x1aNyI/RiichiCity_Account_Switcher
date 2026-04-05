from __future__ import annotations

import sys
import traceback

from services.log_service import LogService
from ui.feedback import show_error
from ui.main_window import main
from utils.paths import ensure_runtime_dirs


def _format_exception(exc: BaseException) -> str:
    return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))


def run() -> None:
    ensure_runtime_dirs()
    logger = LogService.get_logger("Launcher")

    try:
        logger.info("应用启动")
        main()
    except Exception as exc:  # pragma: no cover - GUI 入口兜底
        error_message = _format_exception(exc)
        logger.exception("应用启动失败")
        show_error("程序启动失败", f"{exc}\n\n详细信息已写入日志。")
        sys.stderr.write(error_message)
        raise


if __name__ == "__main__":
    run()
