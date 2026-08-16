from __future__ import annotations

import hashlib
import json
import math
import mimetypes
import re
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

from .attachments import extract_file_text
from .database import Database, utc_now
from .paths import InstallationLayout
from .settings import SettingsService


TOKEN_RE = re.compile(r"[a-z0-9']+")
EMBEDDING_DIMENSIONS = 256
MAX_INDEX_CHARACTERS = 2_000_000


class KnowledgeService:
    """Persistent local document library using deterministic on-device hashed vectors."""

    def __init__(
        self,
        database: Database,
        settings: SettingsService,
        layout: InstallationLayout,
    ) -> None:
        self.database = database
        self.settings = settings
        self.layout = layout

    def add(self, source: str | Path) -> dict[str, Any]:
        if not self.settings.get().knowledge_enabled:
            raise RuntimeError("Knowledge Library is disabled in Settings")
        path = Path(source).expanduser().resolve()
        if not path.is_file():
            raise ValueError("Knowledge source file was not found")
        digest = self._sha256(path)
        with self.database.connect() as connection:
            existing = connection.execute(
                "SELECT * FROM knowledge_documents WHERE sha256 = ?", (digest,)
            ).fetchone()
        if existing:
            return dict(existing)
        safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "-", path.stem).strip("-.") or "document"
        stored = self.layout.knowledge / f"{safe_stem}-{digest[:10]}{path.suffix.lower()}"
        if not stored.exists():
            shutil.copy2(path, stored)
        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        status, text, _metadata = extract_file_text(stored, MAX_INDEX_CHARACTERS)
        now = utc_now()
        with self.database.transaction() as connection:
            cursor = connection.execute(
                "INSERT INTO knowledge_documents(title, source_path, stored_path, sha256, mime_type, size, "
                "parse_status, created_at, indexed_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    path.name,
                    str(path),
                    str(stored),
                    digest,
                    mime_type,
                    path.stat().st_size,
                    status,
                    now,
                    now,
                    now,
                ),
            )
            document_id = int(cursor.lastrowid)
            for index, chunk in enumerate(self._chunks(text)):
                connection.execute(
                    "INSERT INTO knowledge_chunks(document_id, chunk_index, content, embedding_json, created_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (document_id, index, chunk, json.dumps(self._embedding(chunk)), now),
                )
        return self.get(document_id)

    def get(self, document_id: int) -> dict[str, Any]:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT d.*, COUNT(c.id) AS chunk_count FROM knowledge_documents d "
                "LEFT JOIN knowledge_chunks c ON c.document_id = d.id WHERE d.id = ? GROUP BY d.id",
                (document_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"Knowledge document {document_id} was not found")
        return dict(row)

    def list(self, limit: int = 250) -> list[dict[str, Any]]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT d.*, COUNT(c.id) AS chunk_count FROM knowledge_documents d "
                "LEFT JOIN knowledge_chunks c ON c.document_id = d.id GROUP BY d.id "
                "ORDER BY d.updated_at DESC LIMIT ?",
                (max(1, limit),),
            ).fetchall()
        return [dict(row) for row in rows]

    def search(self, query: str, limit: int = 6) -> list[dict[str, Any]]:
        clean = " ".join(query.split()).strip()
        if not clean or not self.settings.get().knowledge_enabled:
            return []
        query_vector = self._embedding(clean)
        query_tokens = Counter(TOKEN_RE.findall(clean.lower()))
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT c.id, c.document_id, c.chunk_index, c.content, c.embedding_json, "
                "d.title, d.stored_path FROM knowledge_chunks c "
                "JOIN knowledge_documents d ON d.id = c.document_id LIMIT 10000"
            ).fetchall()
        scored: list[tuple[float, dict[str, Any]]] = []
        for row in rows:
            item = dict(row)
            try:
                vector = {str(k): float(v) for k, v in json.loads(item.pop("embedding_json")).items()}
            except (json.JSONDecodeError, TypeError, ValueError):
                vector = {}
            chunk_tokens = Counter(TOKEN_RE.findall(item["content"].lower()))
            overlap = sum(min(count, chunk_tokens[token]) for token, count in query_tokens.items())
            score = self._cosine(query_vector, vector) * 8 + overlap * 1.5
            if score > 0:
                item["score"] = round(score, 4)
                scored.append((score, item))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in scored[: max(1, min(limit, 20))]]

    def context(self, query: str, limit: int = 4) -> str:
        results = self.search(query, limit)
        if not results:
            return ""
        return "\n\n".join(
            f"Knowledge: {item['title']} (chunk {int(item['chunk_index']) + 1})\n{item['content']}"
            for item in results
        )

    def reindex(self, document_id: int) -> dict[str, Any]:
        document = self.get(document_id)
        stored = Path(document["stored_path"])
        if not stored.is_file():
            raise FileNotFoundError("The stored knowledge source is missing")
        status, text, _metadata = extract_file_text(stored, MAX_INDEX_CHARACTERS)
        now = utc_now()
        with self.database.transaction() as connection:
            connection.execute("DELETE FROM knowledge_chunks WHERE document_id = ?", (document_id,))
            for index, chunk in enumerate(self._chunks(text)):
                connection.execute(
                    "INSERT INTO knowledge_chunks(document_id, chunk_index, content, embedding_json, created_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (document_id, index, chunk, json.dumps(self._embedding(chunk)), now),
                )
            connection.execute(
                "UPDATE knowledge_documents SET parse_status = ?, indexed_at = ?, updated_at = ? WHERE id = ?",
                (status, now, now, document_id),
            )
        return self.get(document_id)

    def remove(self, document_id: int) -> bool:
        document = self.get(document_id)
        stored = Path(document["stored_path"])
        with self.database.transaction() as connection:
            cursor = connection.execute("DELETE FROM knowledge_documents WHERE id = ?", (document_id,))
        try:
            if stored.parent.resolve() == self.layout.knowledge.resolve():
                stored.unlink(missing_ok=True)
        except OSError:
            pass
        return cursor.rowcount > 0

    @staticmethod
    def _chunks(text: str, size: int = 2_600, overlap: int = 300) -> list[str]:
        clean = text.strip()
        if not clean:
            return []
        chunks: list[str] = []
        start = 0
        while start < len(clean) and len(chunks) < 1000:
            end = min(len(clean), start + size)
            if end < len(clean):
                boundary = max(clean.rfind("\n", start, end), clean.rfind(". ", start, end))
                if boundary > start + size // 2:
                    end = boundary + 1
            chunk = clean[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= len(clean):
                break
            start = max(start + 1, end - overlap)
        return chunks

    @staticmethod
    def _embedding(text: str) -> dict[str, float]:
        counts: Counter[int] = Counter()
        for token in TOKEN_RE.findall(text.lower()):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=4).digest()
            index = int.from_bytes(digest, "big") % EMBEDDING_DIMENSIONS
            counts[index] += 1
        magnitude = math.sqrt(sum(value * value for value in counts.values())) or 1.0
        return {str(index): value / magnitude for index, value in counts.items()}

    @staticmethod
    def _cosine(left: dict[str, float], right: dict[str, float]) -> float:
        return sum(value * right.get(index, 0.0) for index, value in left.items())

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()
