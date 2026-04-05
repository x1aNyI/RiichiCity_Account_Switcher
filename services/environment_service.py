from __future__ import annotations

import os
from dataclasses import dataclass

from services.launch_service import LaunchService
from services.log_service import LogService
from services.registry_service import RegistryService
from services.settings_service import SettingsService


@dataclass(slots=True)
class EnvironmentCheckResult:
    level: str
    message: str


class EnvironmentService:
    def __init__(
        self,
        settings_service: SettingsService | None = None,
        registry_service: RegistryService | None = None,
        launch_service: LaunchService | None = None,
    ) -> None:
        self.settings_service = settings_service or SettingsService()
        self.registry_service = registry_service or RegistryService()
        self.launch_service = launch_service or LaunchService()
        self.logger = LogService.get_logger(self.__class__.__name__)

    def check(self) -> list[EnvironmentCheckResult]:
        results: list[EnvironmentCheckResult] = []

        if os.name == "nt":
            results.append(EnvironmentCheckResult("info", "当前系统为 Windows，可正常使用注册表功能。"))
        else:
            results.append(EnvironmentCheckResult("error", "当前系统不是 Windows，无法使用本工具的注册表能力。"))
            self.logger.error("环境检测失败：当前系统不是 Windows")
            return results

        settings = self.settings_service.load()
        if settings.exe_name.strip():
            results.append(EnvironmentCheckResult("info", f"游戏进程名已配置：{settings.exe_name}"))
        else:
            results.append(EnvironmentCheckResult("warning", "游戏进程名为空，切号时可能无法正确关闭游戏。"))

        try:
            self.registry_service.read_current_account_snapshot()
            results.append(EnvironmentCheckResult("info", "注册表路径可访问。"))
        except FileNotFoundError:
            results.append(EnvironmentCheckResult("warning", "注册表路径当前不存在，请先启动并登录一次游戏。"))
        except OSError as exc:
            results.append(EnvironmentCheckResult("error", f"注册表访问失败：{exc}"))
            self.logger.error("环境检测失败：注册表访问异常：%s", exc)

        if settings.launch_mode == "local":
            if self.launch_service.validate_local_game_path(settings.local_game_path):
                results.append(EnvironmentCheckResult("info", "官网版游戏路径有效。"))
            else:
                results.append(EnvironmentCheckResult("warning", "当前为官网版模式，但游戏路径无效或未配置。"))
        else:
            results.append(EnvironmentCheckResult("info", "当前使用 Steam 启动模式。"))

        self.logger.info("环境检测完成，结果数=%s", len(results))
        return results
