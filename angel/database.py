from __future__ import annotations

import json
import logging
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class AngelConnection(sqlite3.Connection):
    """SQLite context manager that also closes its Windows file handle on exit."""

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> bool:
        try:
            return bool(super().__exit__(exc_type, exc, traceback))
        finally:
            self.close()


class Database:
    """Thread-safe, idempotently migrated SQLite storage for Angel."""

    def __init__(self, path: str | Path, logger: logging.Logger | None = None) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logger or logging.getLogger("angel.database")
        self._write_lock = threading.RLock()
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10, factory=AngelConnection)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")
        connection.execute("PRAGMA synchronous = NORMAL")
        return connection

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self._write_lock:
            connection = self.connect()
            try:
                yield connection
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                connection.close()

    def initialize(self) -> None:
        with self.transaction() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL DEFAULT 'New Conversation',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    sources_json TEXT NOT NULL DEFAULT '[]',
                    attachments_json TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT 'general',
                    title TEXT NOT NULL DEFAULT '',
                    importance INTEGER NOT NULL DEFAULT 3,
                    confidence REAL NOT NULL DEFAULT 0.8,
                    last_used TEXT NOT NULL DEFAULT '',
                    source_conversation_id INTEGER,
                    tags_json TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (source_conversation_id) REFERENCES conversations(id) ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL COLLATE NOCASE UNIQUE,
                    description TEXT NOT NULL DEFAULT '',
                    current_state TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'active',
                    important_files_json TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_activity TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS project_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    kind TEXT NOT NULL DEFAULT 'note',
                    status TEXT NOT NULL DEFAULT 'open',
                    title TEXT NOT NULL DEFAULT '',
                    content TEXT NOT NULL DEFAULT '',
                    file_path TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS conversation_summaries (
                    conversation_id INTEGER PRIMARY KEY,
                    through_message_id INTEGER NOT NULL DEFAULT 0,
                    summary TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS knowledge_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    source_path TEXT NOT NULL DEFAULT '',
                    stored_path TEXT NOT NULL DEFAULT '',
                    sha256 TEXT NOT NULL UNIQUE,
                    mime_type TEXT NOT NULL DEFAULT 'application/octet-stream',
                    size INTEGER NOT NULL DEFAULT 0,
                    parse_status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    indexed_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS knowledge_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    embedding_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (document_id) REFERENCES knowledge_documents(id) ON DELETE CASCADE,
                    UNIQUE(document_id, chunk_index)
                );

                CREATE TABLE IF NOT EXISTS creator_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT NOT NULL,
                    title TEXT NOT NULL DEFAULT '',
                    prompt TEXT NOT NULL DEFAULT '',
                    output_path TEXT NOT NULL DEFAULT '',
                    backend TEXT NOT NULL DEFAULT '',
                    model TEXT NOT NULL DEFAULT '',
                    seed INTEGER,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    status TEXT NOT NULL DEFAULT 'created',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS user_preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS recommendation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mode TEXT NOT NULL,
                    suggestion TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'suggested',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS tool_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    tool TEXT NOT NULL,
                    success INTEGER NOT NULL,
                    metadata TEXT NOT NULL DEFAULT ''
                );

                """
            )
            # Foundation databases may predate source metadata and updated timestamps.
            self._ensure_column(connection, "conversations", "title", "TEXT NOT NULL DEFAULT 'New Conversation'")
            self._ensure_column(connection, "conversations", "created_at", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(connection, "conversations", "updated_at", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(connection, "messages", "sources_json", "TEXT NOT NULL DEFAULT '[]'")
            self._ensure_column(connection, "messages", "attachments_json", "TEXT NOT NULL DEFAULT '[]'")
            self._ensure_column(connection, "messages", "created_at", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(connection, "memories", "text", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(connection, "memories", "category", "TEXT NOT NULL DEFAULT 'general'")
            self._ensure_column(connection, "memories", "created_at", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(connection, "memories", "updated_at", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(connection, "memories", "title", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(connection, "memories", "importance", "INTEGER NOT NULL DEFAULT 3")
            self._ensure_column(connection, "memories", "confidence", "REAL NOT NULL DEFAULT 0.8")
            self._ensure_column(connection, "memories", "last_used", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(connection, "memories", "source_conversation_id", "INTEGER")
            self._ensure_column(connection, "memories", "tags_json", "TEXT NOT NULL DEFAULT '[]'")
            self._ensure_column(connection, "recommendation_history", "mode", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(connection, "recommendation_history", "suggestion", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(connection, "recommendation_history", "status", "TEXT NOT NULL DEFAULT 'suggested'")
            self._ensure_column(connection, "recommendation_history", "created_at", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(connection, "recommendation_history", "updated_at", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(connection, "tool_activity", "timestamp", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(connection, "tool_activity", "tool", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(connection, "tool_activity", "success", "INTEGER NOT NULL DEFAULT 0")
            self._ensure_column(connection, "tool_activity", "metadata", "TEXT NOT NULL DEFAULT ''")
            now = utc_now()
            connection.execute("UPDATE conversations SET created_at = ? WHERE created_at = ''", (now,))
            connection.execute("UPDATE conversations SET updated_at = ? WHERE updated_at = ''", (now,))
            connection.execute("UPDATE messages SET created_at = ? WHERE created_at = ''", (now,))
            connection.execute("UPDATE memories SET created_at = ? WHERE created_at = ''", (now,))
            connection.execute("UPDATE memories SET updated_at = ? WHERE updated_at = ''", (now,))
            connection.execute("UPDATE memories SET last_used = updated_at WHERE last_used = ''")
            connection.execute(
                "UPDATE recommendation_history SET created_at = ? WHERE created_at = ''", (now,)
            )
            connection.execute(
                "UPDATE recommendation_history SET updated_at = ? WHERE updated_at = ''", (now,)
            )
            connection.execute("UPDATE tool_activity SET timestamp = ? WHERE timestamp = ''", (now,))
            connection.executescript(
                """
                CREATE INDEX IF NOT EXISTS idx_messages_conversation
                    ON messages(conversation_id, id);
                CREATE INDEX IF NOT EXISTS idx_memories_updated
                    ON memories(updated_at DESC);
                CREATE INDEX IF NOT EXISTS idx_projects_activity
                    ON projects(last_activity DESC);
                CREATE INDEX IF NOT EXISTS idx_project_items_project
                    ON project_items(project_id, status, updated_at DESC);
                CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_document
                    ON knowledge_chunks(document_id, chunk_index);
                CREATE INDEX IF NOT EXISTS idx_creator_items_created
                    ON creator_items(created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_recommendations_created
                    ON recommendation_history(created_at DESC);
                """
            )
        self.logger.info("Database schema initialized at %s", self.path)

    @staticmethod
    def _ensure_column(
        connection: sqlite3.Connection, table: str, column: str, definition: str
    ) -> None:
        columns = {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
        if column not in columns:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def create_conversation(self, title: str = "New Conversation") -> int:
        now = utc_now()
        with self.transaction() as connection:
            cursor = connection.execute(
                "INSERT INTO conversations(title, created_at, updated_at) VALUES (?, ?, ?)",
                (title.strip() or "New Conversation", now, now),
            )
            return int(cursor.lastrowid)

    def conversation_exists(self, conversation_id: int) -> bool:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM conversations WHERE id = ?", (conversation_id,)
            ).fetchone()
        return row is not None

    def list_conversations(self, limit: int = 100) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT id, title, created_at, updated_at FROM conversations "
                "ORDER BY updated_at DESC, id DESC LIMIT ?",
                (max(1, limit),),
            ).fetchall()
        return [dict(row) for row in rows]

    def search_conversations(self, query: str, limit: int = 100) -> list[dict[str, Any]]:
        clean = " ".join(query.split()).strip()
        if not clean:
            return self.list_conversations(limit)
        pattern = f"%{clean}%"
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT DISTINCT c.id, c.title, c.created_at, c.updated_at "
                "FROM conversations c LEFT JOIN messages m ON m.conversation_id = c.id "
                "WHERE c.title LIKE ? OR m.content LIKE ? "
                "ORDER BY c.updated_at DESC, c.id DESC LIMIT ?",
                (pattern, pattern, max(1, limit)),
            ).fetchall()
        return [dict(row) for row in rows]

    def rename_conversation(self, conversation_id: int, title: str) -> None:
        with self.transaction() as connection:
            connection.execute(
                "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
                (title.strip()[:80] or "New Conversation", utc_now(), conversation_id),
            )

    def delete_conversation(self, conversation_id: int) -> bool:
        """Delete one conversation and its messages through the foreign-key cascade."""
        with self.transaction() as connection:
            cursor = connection.execute(
                "DELETE FROM conversations WHERE id = ?", (conversation_id,)
            )
            return cursor.rowcount > 0

    def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        sources: list[dict[str, Any]] | None = None,
        attachments: list[dict[str, Any]] | None = None,
    ) -> int:
        if role not in {"user", "assistant", "system"}:
            raise ValueError("Unsupported message role")
        now = utc_now()
        serialized_sources = json.dumps(sources or [], ensure_ascii=False)
        serialized_attachments = json.dumps(attachments or [], ensure_ascii=False)
        with self.transaction() as connection:
            cursor = connection.execute(
                "INSERT INTO messages(conversation_id, role, content, sources_json, attachments_json, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    conversation_id,
                    role,
                    content,
                    serialized_sources,
                    serialized_attachments,
                    now,
                ),
            )
            connection.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conversation_id)
            )
            return int(cursor.lastrowid)

    def get_messages(self, conversation_id: int, limit: int = 100) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM (SELECT id, role, content, sources_json, attachments_json, created_at "
                "FROM messages WHERE conversation_id = ? ORDER BY id DESC LIMIT ?) "
                "ORDER BY id ASC",
                (conversation_id, max(1, limit)),
            ).fetchall()
        messages: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            try:
                item["sources"] = json.loads(item.pop("sources_json") or "[]")
            except (json.JSONDecodeError, TypeError):
                item["sources"] = []
                item.pop("sources_json", None)
            try:
                item["attachments"] = json.loads(item.pop("attachments_json") or "[]")
            except (json.JSONDecodeError, TypeError):
                item["attachments"] = []
                item.pop("attachments_json", None)
            messages.append(item)
        return messages

    def last_message(self, conversation_id: int, role: str | None = None) -> dict[str, Any] | None:
        parameters: list[Any] = [conversation_id]
        where = "conversation_id = ?"
        if role:
            where += " AND role = ?"
            parameters.append(role)
        with self.connect() as connection:
            row = connection.execute(
                f"SELECT id, role, content, sources_json, attachments_json, created_at "
                f"FROM messages WHERE {where} ORDER BY id DESC LIMIT 1",
                parameters,
            ).fetchone()
        if row is None:
            return None
        item = dict(row)
        for source, target in (("sources_json", "sources"), ("attachments_json", "attachments")):
            try:
                item[target] = json.loads(item.pop(source) or "[]")
            except (json.JSONDecodeError, TypeError):
                item.pop(source, None)
                item[target] = []
        return item

    def delete_message(self, message_id: int) -> bool:
        with self.transaction() as connection:
            cursor = connection.execute("DELETE FROM messages WHERE id = ?", (message_id,))
            return cursor.rowcount > 0

    def setting_values(self) -> dict[str, str]:
        with self.connect() as connection:
            rows = connection.execute("SELECT key, value FROM settings").fetchall()
        return {str(row["key"]): str(row["value"]) for row in rows}

    def set_settings(self, values: dict[str, str]) -> None:
        with self.transaction() as connection:
            connection.executemany(
                "INSERT INTO settings(key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                [(key, value) for key, value in values.items()],
            )

    def add_tool_activity(self, tool: str, success: bool, metadata: str = "") -> None:
        safe_metadata = " ".join(metadata.split())[:500]
        with self.transaction() as connection:
            connection.execute(
                "INSERT INTO tool_activity(timestamp, tool, success, metadata) VALUES (?, ?, ?, ?)",
                (utc_now(), tool[:80], int(success), safe_metadata),
            )

    def recent_tool_activity(self, limit: int = 20) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT timestamp, tool, success, metadata FROM tool_activity "
                "ORDER BY id DESC LIMIT ?",
                (max(1, min(limit, 100)),),
            ).fetchall()
        return [dict(row) for row in rows]

    def integrity_check(self) -> tuple[bool, str]:
        try:
            with self.connect() as connection:
                row = connection.execute("PRAGMA quick_check").fetchone()
            result = str(row[0] if row else "no result")
            return result.lower() == "ok", result
        except sqlite3.DatabaseError as exc:
            return False, f"{type(exc).__name__}: {exc}"

    def checkpoint(self) -> None:
        with self._write_lock:
            with self.connect() as connection:
                connection.execute("PRAGMA wal_checkpoint(FULL)")

    def backup_to(self, destination: str | Path) -> Path:
        target = Path(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        with self._write_lock:
            source = self.connect()
            backup = sqlite3.connect(target)
            try:
                source.backup(backup)
                backup.commit()
            finally:
                backup.close()
                source.close()
        return target

    def get_conversation_summary(self, conversation_id: int) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT conversation_id, through_message_id, summary, updated_at "
                "FROM conversation_summaries WHERE conversation_id = ?",
                (conversation_id,),
            ).fetchone()
        return dict(row) if row else None

    def set_conversation_summary(
        self, conversation_id: int, through_message_id: int, summary: str
    ) -> None:
        with self.transaction() as connection:
            connection.execute(
                "INSERT INTO conversation_summaries(conversation_id, through_message_id, summary, updated_at) "
                "VALUES (?, ?, ?, ?) ON CONFLICT(conversation_id) DO UPDATE SET "
                "through_message_id = excluded.through_message_id, summary = excluded.summary, "
                "updated_at = excluded.updated_at",
                (conversation_id, through_message_id, summary.strip(), utc_now()),
            )
