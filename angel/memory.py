from __future__ import annotations

import json
import re
from collections import Counter
from difflib import SequenceMatcher
from typing import Any

from .database import Database, utc_now
from .settings import SettingsService


MEMORY_CATEGORIES = (
    "people",
    "preference",
    "dislike",
    "project",
    "goal",
    "task",
    "decision",
    "hardware",
    "software",
    "routine",
    "creative work",
    "idea",
    "important fact",
    "general",
    # Kept for compatibility with earlier Angel memories.
    "person",
)
TOKEN_RE = re.compile(r"[a-z0-9']+")
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "for", "from", "i", "in", "is",
    "it", "my", "of", "on", "that", "the", "this", "to", "with",
}


class MemoryDisabledError(RuntimeError):
    pass


class MemoryService:
    def __init__(self, database: Database, settings: SettingsService) -> None:
        self.database = database
        self.settings = settings

    def add(
        self,
        text: str,
        category: str = "general",
        *,
        title: str = "",
        importance: int = 3,
        confidence: float = 0.8,
        source_conversation_id: int | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        self._require_enabled()
        clean_text = " ".join(text.split()).strip()
        clean_category = category.strip().lower()
        if not clean_text:
            raise ValueError("Memory text cannot be empty")
        if clean_category not in MEMORY_CATEGORIES:
            raise ValueError(f"Unsupported memory category: {category}")
        clean_title = " ".join(title.split()).strip()[:120]
        clean_tags = list(dict.fromkeys(" ".join(tag.split()).strip()[:40] for tag in (tags or []) if tag.strip()))[:20]
        clean_importance = max(1, min(5, int(importance)))
        clean_confidence = max(0.0, min(1.0, float(confidence)))
        now = utc_now()
        with self.database.transaction() as connection:
            candidates = connection.execute(
                "SELECT id, text, category FROM memories ORDER BY updated_at DESC LIMIT 500"
            ).fetchall()
            existing_id: int | None = None
            normalized = self._normalized(clean_text)
            for candidate in candidates:
                other = self._normalized(str(candidate["text"]))
                if other == normalized or (
                    str(candidate["category"]) == clean_category
                    and
                    len(normalized) >= 20
                    and SequenceMatcher(None, normalized, other).ratio() >= 0.9
                ):
                    existing_id = int(candidate["id"])
                    break
            if existing_id is not None:
                connection.execute(
                    "UPDATE memories SET text = ?, category = ?, title = CASE WHEN ? = '' THEN title ELSE ? END, "
                    "importance = MAX(importance, ?), confidence = MAX(confidence, ?), last_used = ?, "
                    "source_conversation_id = COALESCE(?, source_conversation_id), tags_json = ?, updated_at = ? "
                    "WHERE id = ?",
                    (
                        clean_text,
                        clean_category,
                        clean_title,
                        clean_title,
                        clean_importance,
                        clean_confidence,
                        now,
                        source_conversation_id,
                        json.dumps(clean_tags),
                        now,
                        existing_id,
                    ),
                )
                memory_id = existing_id
            else:
                cursor = connection.execute(
                    "INSERT INTO memories(text, category, title, importance, confidence, last_used, "
                    "source_conversation_id, tags_json, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        clean_text,
                        clean_category,
                        clean_title,
                        clean_importance,
                        clean_confidence,
                        now,
                        source_conversation_id,
                        json.dumps(clean_tags),
                        now,
                        now,
                    ),
                )
                memory_id = int(cursor.lastrowid)
        return self.get(memory_id)

    def get(self, memory_id: int) -> dict[str, Any]:
        with self.database.connect() as connection:
            row = connection.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
        if row is None:
            raise KeyError(f"Memory {memory_id} was not found")
        return self._item(row)

    def list(self, query: str = "", limit: int = 100) -> list[dict[str, Any]]:
        self._require_enabled()
        if query.strip():
            return self.search(query, limit=limit)
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM memories ORDER BY importance DESC, updated_at DESC, id DESC LIMIT ?",
                (max(1, limit),),
            ).fetchall()
        return [self._item(row) for row in rows]

    def search(self, query: str, limit: int = 8) -> list[dict[str, Any]]:
        self._require_enabled()
        query_tokens = self._tokens(query)
        if not query_tokens:
            return self.list(limit=limit)
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM memories ORDER BY updated_at DESC, id DESC LIMIT 1000"
            ).fetchall()
        scored: list[tuple[float, dict[str, Any]]] = []
        token_counts = Counter(query_tokens)
        lowered_query = query.lower().strip()
        for recency_rank, row in enumerate(rows):
            item = self._item(row)
            memory_tokens = self._tokens(
                f"{item['category']} {item['title']} {item['text']} {' '.join(item['tags'])}"
            )
            overlap = sum(min(token_counts[token], memory_tokens.count(token)) for token in token_counts)
            phrase_bonus = 3 if lowered_query in item["text"].lower() else 0
            category_bonus = 1 if item["category"] in query_tokens else 0
            if overlap or phrase_bonus or category_bonus:
                score = (
                    overlap * 4
                    + phrase_bonus
                    + category_bonus
                    + int(item["importance"]) * 0.35
                    + float(item["confidence"]) * 0.5
                    + 1 / (recency_rank + 2)
                )
                scored.append((score, item))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        selected = [item for _, item in scored[: max(1, limit)]]
        if selected:
            now = utc_now()
            with self.database.transaction() as connection:
                connection.executemany(
                    "UPDATE memories SET last_used = ? WHERE id = ?",
                    [(now, int(item["id"])) for item in selected],
                )
        return selected

    def update(self, memory_id: int, **changes: Any) -> dict[str, Any]:
        current = self.get(memory_id)
        text = " ".join(str(changes.get("text", current["text"])).split()).strip()
        category = str(changes.get("category", current["category"])).strip().lower()
        if not text:
            raise ValueError("Memory text cannot be empty")
        if category not in MEMORY_CATEGORIES:
            raise ValueError("Unsupported memory category")
        tags = list(changes.get("tags", current["tags"]))
        with self.database.transaction() as connection:
            connection.execute(
                "UPDATE memories SET text = ?, category = ?, title = ?, importance = ?, confidence = ?, "
                "source_conversation_id = ?, tags_json = ?, updated_at = ? WHERE id = ?",
                (
                    text,
                    category,
                    " ".join(str(changes.get("title", current["title"])).split())[:120],
                    max(1, min(5, int(changes.get("importance", current["importance"])))),
                    max(0.0, min(1.0, float(changes.get("confidence", current["confidence"])))),
                    changes.get("source_conversation_id", current["source_conversation_id"]),
                    json.dumps(tags),
                    utc_now(),
                    memory_id,
                ),
            )
        return self.get(memory_id)

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

    @staticmethod
    def _normalized(text: str) -> str:
        return " ".join(TOKEN_RE.findall(text.lower()))

    @staticmethod
    def _item(row: Any) -> dict[str, Any]:
        item = dict(row)
        try:
            item["tags"] = json.loads(item.pop("tags_json") or "[]")
        except (json.JSONDecodeError, TypeError):
            item.pop("tags_json", None)
            item["tags"] = []
        return item
