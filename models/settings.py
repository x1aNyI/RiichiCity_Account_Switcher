from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class Settings:
    launch_mode: str = "steam"
    local_game_path: str = ""
    exe_name: str = "Mahjong-JP.exe"

    def to_dict(self) -> dict[str, Any]:
        return {
            "launch_mode": self.launch_mode,
            "local_game_path": self.local_game_path,
            "exe_name": self.exe_name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Settings":
        return cls(
            launch_mode=str(data.get("launch_mode", "steam")),
            local_game_path=str(data.get("local_game_path", "")),
            exe_name=str(data.get("exe_name", "Mahjong-JP.exe")),
        )
