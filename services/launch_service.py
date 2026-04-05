from __future__ import annotations

import os
import subprocess
from pathlib import Path

from models.settings import Settings
from services.log_service import LogService

STEAM_APP_URL = "steam://rungameid/1954420"


class LaunchService:
    def __init__(self) -> None:
        self.logger = LogService.get_logger(self.__class__.__name__)

    def launch_game(self, settings: Settings) -> None:
        if settings.launch_mode == "steam":
            self.logger.info("使用 Steam 方式启动游戏：%s", STEAM_APP_URL)
            os.startfile(STEAM_APP_URL)
            return

        game_path = Path(settings.local_game_path)
        if not game_path.exists() or not game_path.is_file():
            self.logger.error("官网版游戏路径无效：%s", settings.local_game_path)
            raise FileNotFoundError("官网版游戏路径无效，请先配置正确的 .exe 文件路径。")

        self.logger.info("使用官网版路径启动游戏：%s", game_path)
        subprocess.Popen([str(game_path)])

    def validate_local_game_path(self, path: str) -> bool:
        if not path:
            return False
        game_path = Path(path)
        is_valid = game_path.exists() and game_path.is_file()
        self.logger.info("校验官网版路径：path=%s, is_valid=%s", path, is_valid)
        return is_valid
