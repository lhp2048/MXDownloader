import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class EngineProgress:
    progress: float = 0.0
    speed: str = ""
    file_path: str = ""
    file_size: int = 0
    title: str = ""
    status: Optional[str] = None
    error_message: str = ""


class DownloadEngine(ABC):
    name: str = "base"

    @abstractmethod
    async def is_available(self) -> bool:
        pass

    @abstractmethod
    async def start(
        self,
        task_id: int,
        url: str,
        output_dir: str,
        options: dict[str, Any],
    ) -> str:
        """Start download and return engine_task_id (may be empty)."""
        pass

    @abstractmethod
    async def poll(self, engine_task_id: str, task_id: int) -> EngineProgress:
        pass

    @abstractmethod
    async def pause(self, engine_task_id: str, task_id: int) -> bool:
        pass

    @abstractmethod
    async def cancel(self, engine_task_id: str, task_id: int) -> bool:
        pass


def serialize_options(options: dict[str, Any]) -> str:
    return json.dumps(options, ensure_ascii=False)


def parse_options(options_json: str) -> dict[str, Any]:
    if not options_json:
        return {}
    try:
        return json.loads(options_json)
    except json.JSONDecodeError:
        return {}
