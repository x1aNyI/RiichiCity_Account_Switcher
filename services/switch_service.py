from __future__ import annotations

from models.account import Account
from models.settings import Settings
from services.launch_service import LaunchService
from services.log_service import LogService
from services.process_service import ProcessService
from services.registry_service import RegistryService


class SwitchService:
    def __init__(
        self,
        process_service: ProcessService | None = None,
        registry_service: RegistryService | None = None,
        launch_service: LaunchService | None = None,
    ) -> None:
        self.process_service = process_service or ProcessService()
        self.registry_service = registry_service or RegistryService()
        self.launch_service = launch_service or LaunchService()
        self.logger = LogService.get_logger(self.__class__.__name__)

    def switch_account(self, account: Account, settings: Settings) -> None:
        self.logger.info("开始切号：account_id=%s, remark=%s", account.account_id, account.remark)
        if self.process_service.is_process_running(settings.exe_name):
            self.logger.info("检测到游戏进程运行中，准备关闭：exe_name=%s", settings.exe_name)
            self.process_service.kill_process(settings.exe_name)
            if not self.process_service.wait_for_process_exit(settings.exe_name, timeout=15):
                self.logger.error("游戏进程未在超时时间内退出：exe_name=%s", settings.exe_name)
                raise TimeoutError("游戏进程在 15 秒内未能完全退出，请手动关闭后重试。")

        self.registry_service.write_account_snapshot(account.registry_values)
        self.logger.info("账号注册表写入完成：account_id=%s", account.account_id)
        self.launch_service.launch_game(settings)
        self.logger.info("切号完成并已启动游戏：account_id=%s", account.account_id)
