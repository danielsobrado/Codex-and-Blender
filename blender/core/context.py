from __future__ import annotations

from pathlib import Path
from typing import Any


class JobContext:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    def section(self, name: str) -> dict[str, Any]:
        value = self.config.get(name)
        if not isinstance(value, dict):
            raise ValueError(f"Config section '{name}' is missing or invalid.")
        return value

    def list_section(self, name: str) -> list[dict[str, Any]]:
        value = self.config.get(name)
        if not isinstance(value, list):
            raise ValueError(f"Config section '{name}' is missing or invalid.")
        return value

    def path(self, name: str) -> Path:
        value = self.section("paths").get(name)
        if not value:
            raise ValueError(f"Config path '{name}' is missing.")
        return Path(value)
