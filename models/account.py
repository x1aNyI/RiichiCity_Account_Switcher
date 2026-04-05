from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class Account:
    account_id: str
    remark: str
    registry_values: dict[str, dict[str, Any]] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "account_id": self.account_id,
            "remark": self.remark,
            "registry_values": self.registry_values,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Account":
        return cls(
            account_id=str(data.get("account_id", "")),
            remark=str(data.get("remark", "")),
            registry_values=dict(data.get("registry_values", {})),
            created_at=str(data.get("created_at", datetime.now().isoformat(timespec="seconds"))),
            updated_at=str(data.get("updated_at", datetime.now().isoformat(timespec="seconds"))),
        )
