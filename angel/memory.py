from __future__ import annotations

import re
from collections import Counter
from typing import Any

from .database import Database, utc_now
from .settings import SettingsService


MEMORY_CATEGORIES = (
    "preference",
    "dislike",
    "project",
    "goal",
    "routine",
    "person",
    "general",
)
TOKEN_RE = re.compile(r"[a-z0-9']+")
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "for",
    "from",
    "i",
    "in",
    "is",
    "it",
    "my",
    "of",
    "on",
    "that",
    "the",
    "this",
    "to",
    "with",
}


class MemoryDisabledError(RuntimeError):
    pass


class MemoryService:
    def __init__(self, database: Database, settings: SettingsService) -> None:
        self.database = database
        self.settings = settings

    def add(self, text: str, category: str = "general") -> dict[str, Any]:
        self._require_enabled()
        clean_text = " ".join(text.split()).strip()
        clean_category = category.strip().lower()
        if not clean_text:
            raise ValueError("Memory text cannot be empty")
        if clean_category not in MEMORY_CATEGORIES:
            raise ValueError(f"Unsupported memory category: {category}")
        now = utc_now()
        with self.database.transaction() as connection:
            existing = connection.execute(
                "SELECT id FROM memories WHERE lower(text) = lower(?)", (clean_text,)
            ).fetchone()
            if existing:
                memory_id = int(existing["id"])
                connection.execute(
                    "UPDATE memories SET category = ?, updated_at = ? WHERE id = ?",
                    (clean_category, now, memory_id),
                )
            else:
                cursor = connection.execute(
                    "INSERT INTO memories(text, category, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (clean_text, clean_category, now, now),
                )
                memory_id = int(cursor.lastrowid)
        return self.get(memory_id)

    def get(self, memory_id: int) -> dict[str, Any]:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT id, text, category, created_at, updated_at FROM memories WHERE id = ?",
                (memory_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"Memory {memory_id} was not found")
        return dict(row)

    def list(self, query: str = "", limit: int = 100) -> list[dict[str, Any]]:
        self._require_enabled()
        if query.strip():
            return self.search(query, limit=limit)
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT id, text, category, created_at, updated_at FROM memories "
                "ORDER BY updated_at DESC, id DESC LIMIT ?",
                (max(1, limit),),
            ).fetchall()
        return [dict(row) for row in rows]

    def search(self, query: str, limit: int = 8) -> list[dict[str, Any]]:
        self._require_enabled()
        query_tokens = self._tokens(query)
        if not query_tokens:
            return self.list(limit=limit)
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT id, text, category, created_at, updated_at FROM memories "
                "ORDER BY updated_at DESC, id DESC LIMIT 500"
            ).fetchall()
        scored: list[tuple[float, dict[str, Any]]] = []
        token_counts = Counter(query_tokens)
        for recency_rank, row in enumerate(rows):
            item = dict(row)
            memory_tokens = self._tokens(f"{item['category']} {item['text']}")
            overlap = sum(min(token_counts[token], memory_tokens.count(token)) for token in token_counts)
            phrase_bonus = 3 if query.lower().strip() in item["text"].lower() else 0
            category_bonus = 1 if item["category"] in query_tokens else 0
            if overlap or phrase_bonus or category_bonus:
                score = overlap * 4 + phrase_bonus + category_bonus + 1 / (recency_rank + 2)
                scored.append((score, item))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in scored[: max(1, limit)]]

    def delete(self, memory_id: int) -> bool:
        self._require_enabled()
        with self.database.transaction() as connection:
            cursor = connection.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            return cursor.rowcount > 0

    def _require_enabled(self) -> None:
        if not self.settings.get().memory_enabled:
            raise MemoryDisabledError("Memory is disabled in Angel Settings")

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return [token for token in TOKEN_RE.findall(text.lower()) if token not in STOP_WORDS]
