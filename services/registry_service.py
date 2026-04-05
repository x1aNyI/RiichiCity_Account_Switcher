from __future__ import annotations

import winreg
from typing import Any

from services.log_service import LogService

REGISTRY_ROOT = winreg.HKEY_CURRENT_USER
REGISTRY_PATH = r"SOFTWARE\HappyWoods\RiichiCity"

REG_TYPE_TO_NAME = {
    winreg.REG_SZ: "REG_SZ",
    winreg.REG_EXPAND_SZ: "REG_EXPAND_SZ",
    winreg.REG_DWORD: "REG_DWORD",
    winreg.REG_QWORD: "REG_QWORD",
    winreg.REG_BINARY: "REG_BINARY",
    winreg.REG_MULTI_SZ: "REG_MULTI_SZ",
}

REG_NAME_TO_TYPE = {value: key for key, value in REG_TYPE_TO_NAME.items()}


class RegistryService:
    def __init__(self) -> None:
        self.logger = LogService.get_logger(self.__class__.__name__)

    def read_current_account_snapshot(self) -> dict[str, dict[str, Any]]:
        snapshot: dict[str, dict[str, Any]] = {}
        self.logger.info("开始读取注册表快照：%s", REGISTRY_PATH)
        try:
            with winreg.OpenKey(REGISTRY_ROOT, REGISTRY_PATH, 0, winreg.KEY_READ) as registry_key:
                index = 0
                while True:
                    try:
                        value_name, value_data, value_type = winreg.EnumValue(registry_key, index)
                        snapshot[value_name] = {
                            "type": REG_TYPE_TO_NAME.get(value_type, str(value_type)),
                            "value": self._serialize_value(value_data, value_type),
                        }
                        index += 1
                    except OSError:
                        break
        except FileNotFoundError:
            self.logger.warning("注册表路径不存在：%s", REGISTRY_PATH)
            raise

        self.logger.info("读取注册表快照完成，项目数=%s", len(snapshot))
        return snapshot

    def write_account_snapshot(self, snapshot: dict[str, dict[str, Any]]) -> None:
        self.logger.info("开始写入注册表快照，项目数=%s", len(snapshot))
        with winreg.CreateKeyEx(REGISTRY_ROOT, REGISTRY_PATH, 0, winreg.KEY_SET_VALUE) as registry_key:
            for value_name, payload in snapshot.items():
                value_type_name = str(payload.get("type", "REG_SZ"))
                value_type = REG_NAME_TO_TYPE.get(value_type_name, winreg.REG_SZ)
                value_data = self._deserialize_value(payload.get("value"), value_type)
                winreg.SetValueEx(registry_key, value_name, 0, value_type, value_data)
        self.logger.info("注册表快照写入完成")

    def _serialize_value(self, value: Any, value_type: int) -> Any:
        if value_type == winreg.REG_BINARY:
            return list(value)
        return value

    def _deserialize_value(self, value: Any, value_type: int) -> Any:
        if value_type == winreg.REG_BINARY:
            return bytes(value)
        return value
