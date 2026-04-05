from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from models.account import Account
from services.log_service import LogService
from utils.paths import ACCOUNT_ORDER_FILE, DATA_DIR


class AccountOrderService:
    def __init__(self, order_file: Path = ACCOUNT_ORDER_FILE) -> None:
        self.order_file = order_file
        self.logger = LogService.get_logger(self.__class__.__name__)

    def ensure_storage(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not self.order_file.exists():
            self._write_payload([])
            self.logger.info("初始化账号顺序文件：%s", self.order_file)

    def load_ordered_ids(self) -> list[str]:
        self.ensure_storage()

        try:
            data = json.loads(self.order_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            self.logger.warning("账号顺序文件损坏，已回退到默认顺序：%s", exc)
            self._write_payload([])
            return []
        except OSError as exc:
            self.logger.warning("读取账号顺序文件失败，已回退到默认顺序：%s", exc)
            return []

        ordered_account_ids = data.get("ordered_account_ids")
        if not isinstance(ordered_account_ids, list):
            self.logger.warning("账号顺序文件字段异常，已回退到默认顺序")
            self._write_payload([])
            return []

        normalized_ids: list[str] = []
        for item in ordered_account_ids:
            account_id = str(item).strip()
            if account_id and account_id not in normalized_ids:
                normalized_ids.append(account_id)

        if normalized_ids != ordered_account_ids:
            self.logger.info("账号顺序文件已自动规范化")
            self._write_payload(normalized_ids)

        return normalized_ids

    def apply_order(self, accounts: list[Account]) -> list[Account]:
        ordered_ids = self.load_ordered_ids()
        account_map = {account.account_id: account for account in accounts}

        ordered_accounts = [account_map[account_id] for account_id in ordered_ids if account_id in account_map]
        missing_accounts = [account for account in accounts if account.account_id not in ordered_ids]
        normalized_accounts = ordered_accounts + missing_accounts
        normalized_ids = [account.account_id for account in normalized_accounts]

        if normalized_ids != ordered_ids:
            self.save_order(normalized_ids)

        return normalized_accounts

    def append_account(self, account_id: str) -> None:
        ordered_ids = self.load_ordered_ids()
        normalized_account_id = account_id.strip()
        if not normalized_account_id:
            return
        if normalized_account_id in ordered_ids:
            return
        ordered_ids.append(normalized_account_id)
        self.save_order(ordered_ids)

    def remove_account(self, account_id: str) -> None:
        ordered_ids = self.load_ordered_ids()
        filtered_ids = [item for item in ordered_ids if item != account_id]
        if filtered_ids == ordered_ids:
            return
        self.save_order(filtered_ids)

    def move_account(self, account_id: str, target_index: int) -> bool:
        ordered_ids = self.load_ordered_ids()
        if account_id not in ordered_ids:
            return False

        current_index = ordered_ids.index(account_id)
        bounded_index = max(0, min(target_index, len(ordered_ids) - 1))
        if current_index == bounded_index:
            return False

        ordered_ids.pop(current_index)
        ordered_ids.insert(bounded_index, account_id)
        self.save_order(ordered_ids)
        return True

    def sync_with_accounts(self, accounts: list[Account]) -> list[Account]:
        return self.apply_order(accounts)

    def _write_payload(self, ordered_ids: list[str]) -> None:
        payload = {
            "version": 1,
            "ordered_account_ids": ordered_ids,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
        self.order_file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def save_order(self, ordered_ids: list[str]) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        normalized_ids: list[str] = []
        for item in ordered_ids:
            account_id = str(item).strip()
            if account_id and account_id not in normalized_ids:
                normalized_ids.append(account_id)
        self._write_payload(normalized_ids)
        self.logger.info("保存账号顺序，数量=%s", len(normalized_ids))
