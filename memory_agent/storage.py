import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Iterable

from .models import Memory


class MemoryStore:
    """Small SQLite store with deterministic lexical retrieval.

    It deliberately has no provider-specific code, so it can be reused by
    OpenAI, Anthropic, Gemini, local models, or a non-LLM workflow.
    """

    def __init__(self, path: str | Path = "data/memory.db") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path)) as conn:
            with conn:
                conn.execute(
                """CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY, content TEXT NOT NULL, kind TEXT NOT NULL,
                    importance INTEGER NOT NULL, source TEXT NOT NULL,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                )"""
            )

    def save(self, memory: Memory) -> Memory:
        with closing(sqlite3.connect(self.path)) as conn:
            with conn:
                conn.execute(
                """INSERT INTO memories
                   (id, content, kind, importance, source, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET content=excluded.content,
                   kind=excluded.kind, importance=excluded.importance,
                   source=excluded.source, updated_at=excluded.updated_at""",
                (memory.id, memory.content, memory.kind, memory.importance,
                 memory.source, memory.created_at, memory.updated_at),
            )
        return memory

    def delete(self, memory_id: str) -> None:
        with closing(sqlite3.connect(self.path)) as conn:
            with conn:
                conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))

    def all(self) -> list[Memory]:
        with closing(sqlite3.connect(self.path)) as conn:
            rows = conn.execute(
                    "SELECT id, content, kind, importance, source, created_at, updated_at "
                    "FROM memories ORDER BY importance DESC, updated_at DESC"
                ).fetchall()
        return [Memory(*row[1:3], importance=row[3], source=row[4], id=row[0],
                       created_at=row[5], updated_at=row[6]) for row in rows]

    def search(self, query: str, limit: int = 8) -> list[Memory]:
        terms = {term.lower() for term in query.split() if len(term) > 1}
        candidates = self.all()
        scored: list[tuple[float, Memory]] = []
        for memory in candidates:
            haystack = f"{memory.content} {memory.kind}".lower()
            score = sum(1 for term in terms if term in haystack)
            if score:
                scored.append((score + memory.importance * 0.05, memory))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [memory for _, memory in scored[:limit]]

    def export_json(self, path: str | Path) -> None:
        Path(path).write_text(
            json.dumps([item.as_dict() for item in self.all()], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
