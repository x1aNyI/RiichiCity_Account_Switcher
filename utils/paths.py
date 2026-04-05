from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "MahjongSwitcher"


def get_app_dir() -> Path:
    """获取程序所在目录（兼容 PyInstaller 打包后的 exe）。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def get_user_data_root() -> Path:
    """获取用户数据根目录，优先使用 LocalAppData。"""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / APP_NAME
    return get_app_dir()


def ensure_runtime_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


APP_DIR = get_app_dir()
USER_DATA_DIR = get_user_data_root()
DATA_DIR = USER_DATA_DIR / "data"
SETTINGS_FILE = DATA_DIR / "settings.json"
ACCOUNTS_FILE = DATA_DIR / "accounts.json"
ACCOUNT_ORDER_FILE = DATA_DIR / "account_order.json"
LOGS_DIR = USER_DATA_DIR / "logs"
