from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from models.account import Account
from services.log_service import LogService
from utils.paths import ACCOUNTS_FILE, DATA_DIR


class AccountService:
    def __init__(self, accounts_file: Path = ACCOUNTS_FILE) -> None:
        self.accounts_file = accounts_file
        self.logger = LogService.get_logger(self.__class__.__name__)

    def ensure_storage(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not self.accounts_file.exists():
            self.accounts_file.write_text("[]", encoding="utf-8")
            self.logger.info("初始化账号数据文件：%s", self.accounts_file)

    def load_all(self) -> list[Account]:
        self.ensure_storage()
        data = json.loads(self.accounts_file.read_text(encoding="utf-8"))
        accounts = [Account.from_dict(item) for item in data]
        self.logger.info("加载账号列表，数量=%s", len(accounts))
        return accounts

    def save_all(self, accounts: list[Account]) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        payload = [account.to_dict() for account in accounts]
        self.accounts_file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.logger.info("保存账号列表，数量=%s", len(accounts))

    def add_account(self, remark: str, registry_values: dict[str, dict[str, object]]) -> Account:
        accounts = self.load_all()
        account = Account(
            account_id=str(uuid4()),
            remark=remark,
            registry_values=registry_values,
        )
        accounts.append(account)
        self.save_all(accounts)
        self.logger.info("新增账号：account_id=%s, remark=%s", account.account_id, account.remark)
        return account

    def update_remark(self, account_id: str, new_remark: str) -> Account:
        accounts = self.load_all()
        for account in accounts:
            if account.account_id == account_id:
                old_remark = account.remark
                account.remark = new_remark
                account.updated_at = datetime.now().isoformat(timespec="seconds")
                self.save_all(accounts)
                self.logger.info(
                    "更新账号备注：account_id=%s, old_remark=%s, new_remark=%s",
                    account_id,
                    old_remark,
                    new_remark,
                )
                return account
        self.logger.warning("更新账号备注失败，未找到账号：account_id=%s", account_id)
        raise ValueError(f"未找到账号：{account_id}")

    def delete_account(self, account_id: str) -> None:
        accounts = self.load_all()
        filtered_accounts = [account for account in accounts if account.account_id != account_id]
        self.save_all(filtered_accounts)
        self.logger.info("删除账号：account_id=%s", account_id)

