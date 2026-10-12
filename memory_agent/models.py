from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
import uuid


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Memory:
    content: str
    kind: str = "fact"
    importance: int = 3
    source: str = "user"
    id: str = ""
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        self.id = self.id or str(uuid.uuid4())
        now = utc_now()
        self.created_at = self.created_at or now
        self.updated_at = self.updated_at or self.created_at
        self.importance = max(1, min(5, int(self.importance)))

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Memory":
        return cls(**value)
