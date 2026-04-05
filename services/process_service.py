from __future__ import annotations

import subprocess
import time


class ProcessService:
    def is_process_running(self, exe_name: str) -> bool:
        result = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {exe_name}"],
            capture_output=True,
            text=True,
        )
        return exe_name.lower() in result.stdout.lower()

    def wait_for_process_exit(self, exe_name: str, timeout: int = 15) -> bool:
        for _ in range(timeout * 2):
            if not self.is_process_running(exe_name):
                return True
            time.sleep(0.5)
        return False

    def kill_process(self, exe_name: str) -> None:
        subprocess.run(
            ["taskkill", "/F", "/IM", exe_name, "/T"],
            capture_output=True,
            text=True,
        )
