from __future__ import annotations

import json
from pathlib import Path

from models.settings import Settings
from services.log_service import LogService
from utils.paths import DATA_DIR, SETTINGS_FILE


class SettingsService:
    def __init__(self, settings_file: Path = SETTINGS_FILE) -> None:
        self.settings_file = settings_file
        self.logger = LogService.get_logger(self.__class__.__name__)

    def ensure_storage(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not self.settings_file.exists():
            self.save(Settings())
            self.logger.info("初始化设置文件：%s", self.settings_file)

    def load(self) -> Settings:
        self.ensure_storage()
        data = json.loads(self.settings_file.read_text(encoding="utf-8"))
        settings = Settings.from_dict(data)
        self.logger.info("加载设置：launch_mode=%s", settings.launch_mode)
        return settings

    def save(self, settings: Settings) -> Settings:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.settings_file.write_text(
            json.dumps(settings.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.logger.info(
            "保存设置：launch_mode=%s, local_game_path=%s, exe_name=%s",
            settings.launch_mode,
            settings.local_game_path,
            settings.exe_name,
        )
        return settings
