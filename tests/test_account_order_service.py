import json
import tempfile
import unittest
from pathlib import Path

from models.account import Account
from services.account_order_service import AccountOrderService


class AccountOrderServiceTestCase(unittest.TestCase):
    def create_account(self, account_id: str, remark: str) -> Account:
        return Account(account_id=account_id, remark=remark)

    def test_apply_order_uses_saved_order_and_appends_missing_accounts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = AccountOrderService(order_file=Path(temp_dir) / "account_order.json")
            service.save_order(["b", "a"])

            accounts = [
                self.create_account("a", "账号A"),
                self.create_account("b", "账号B"),
                self.create_account("c", "账号C"),
            ]

            ordered_accounts = service.apply_order(accounts)

            self.assertEqual([account.account_id for account in ordered_accounts], ["b", "a", "c"])

    def test_apply_order_recovers_from_invalid_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            order_file = Path(temp_dir) / "account_order.json"
            order_file.write_text('{"ordered_account_ids": "bad"}', encoding="utf-8")
            service = AccountOrderService(order_file=order_file)

            accounts = [
                self.create_account("a", "账号A"),
                self.create_account("b", "账号B"),
            ]

            ordered_accounts = service.apply_order(accounts)

            self.assertEqual([account.account_id for account in ordered_accounts], ["a", "b"])
            payload = json.loads(order_file.read_text(encoding="utf-8"))
            self.assertEqual(payload["ordered_account_ids"], ["a", "b"])

    def test_move_account_reorders_existing_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = AccountOrderService(order_file=Path(temp_dir) / "account_order.json")
            service.save_order(["a", "b", "c"])

            changed = service.move_account("c", 0)

            self.assertTrue(changed)
            self.assertEqual(service.load_ordered_ids(), ["c", "a", "b"])

    def test_remove_account_deletes_invalid_id_from_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = AccountOrderService(order_file=Path(temp_dir) / "account_order.json")
            service.save_order(["a", "b", "c"])

            service.remove_account("b")

            self.assertEqual(service.load_ordered_ids(), ["a", "c"])


if __name__ == "__main__":
    unittest.main()
