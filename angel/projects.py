from __future__ import annotations

import json
import re
from collections import Counter
from typing import Any

from .database import Database, utc_now
from .settings import SettingsService


PROJECT_ITEM_KINDS = ("decision", "todo", "completed", "idea", "note", "file", "activity")
PROJECT_STATUSES = ("active", "paused", "completed", "archived")
TOKEN_RE = re.compile(r"[a-z0-9']+")


class ProjectService:
    def __init__(self, database: Database, settings: SettingsService) -> None:
        self.database = database
        self.settings = settings

    def create(self, name: str, description: str = "") -> dict[str, Any]:
        clean_name = " ".join(name.split()).strip()[:120]
        if not clean_name:
            raise ValueError("Project name cannot be empty")
        now = utc_now()
        with self.database.transaction() as connection:
            existing = connection.execute(
                "SELECT id FROM projects WHERE lower(name) = lower(?)", (clean_name,)
            ).fetchone()
            if existing:
                project_id = int(existing["id"])
                if description.strip():
                    connection.execute(
                        "UPDATE projects SET description = ?, updated_at = ?, last_activity = ? WHERE id = ?",
                        (" ".join(description.split()).strip(), now, now, project_id),
                    )
            else:
                cursor = connection.execute(
                    "INSERT INTO projects(name, description, current_state, status, important_files_json, "
                    "created_at, updated_at, last_activity) VALUES (?, ?, '', 'active', '[]', ?, ?, ?)",
                    (clean_name, description.strip(), now, now, now),
                )
                project_id = int(cursor.lastrowid)
        return self.get(project_id)

    def get(self, project_id: int) -> dict[str, Any]:
        with self.database.connect() as connection:
            row = connection.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if row is None:
            raise KeyError(f"Project {project_id} was not found")
        return self._project(row)

    def list(self, query: str = "", limit: int = 100) -> list[dict[str, Any]]:
        clean = " ".join(query.split()).strip()
        with self.database.connect() as connection:
            if clean:
                pattern = f"%{clean}%"
                rows = connection.execute(
                    "SELECT DISTINCT p.* FROM projects p LEFT JOIN project_items i ON i.project_id = p.id "
                    "WHERE p.name LIKE ? OR p.description LIKE ? OR p.current_state LIKE ? "
                    "OR i.title LIKE ? OR i.content LIKE ? ORDER BY p.last_activity DESC LIMIT ?",
                    (pattern, pattern, pattern, pattern, pattern, max(1, limit)),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM projects ORDER BY CASE status WHEN 'active' THEN 0 ELSE 1 END, "
                    "last_activity DESC LIMIT ?",
                    (max(1, limit),),
                ).fetchall()
        return [self._project(row) for row in rows]

    def update(self, project_id: int, **changes: Any) -> dict[str, Any]:
        current = self.get(project_id)
        name = " ".join(str(changes.get("name", current["name"])).split()).strip()[:120]
        status = str(changes.get("status", current["status"])).strip().lower()
        if not name:
            raise ValueError("Project name cannot be empty")
        if status not in PROJECT_STATUSES:
            raise ValueError("Unsupported project status")
        files = changes.get("important_files", current["important_files"])
        clean_files = list(dict.fromkeys(str(path) for path in files if str(path).strip()))[:100]
        now = utc_now()
        with self.database.transaction() as connection:
            connection.execute(
                "UPDATE projects SET name = ?, description = ?, current_state = ?, status = ?, "
                "important_files_json = ?, updated_at = ?, last_activity = ? WHERE id = ?",
                (
                    name,
                    str(changes.get("description", current["description"])).strip(),
                    str(changes.get("current_state", current["current_state"])).strip(),
                    status,
                    json.dumps(clean_files),
                    now,
                    now,
                    project_id,
                ),
            )
        return self.get(project_id)

    def delete(self, project_id: int) -> bool:
        with self.database.transaction() as connection:
            cursor = connection.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        if self.active_project_id() == project_id:
            self.set_active(None)
        return cursor.rowcount > 0

    def add_item(
        self,
        project_id: int,
        kind: str,
        title: str,
        content: str = "",
        status: str = "open",
        file_path: str = "",
    ) -> dict[str, Any]:
        self.get(project_id)
        clean_kind = kind.strip().lower()
        if clean_kind not in PROJECT_ITEM_KINDS:
            raise ValueError("Unsupported project item type")
        clean_title = " ".join(title.split()).strip()[:160]
        if not clean_title:
            raise ValueError("Project item title cannot be empty")
        now = utc_now()
        with self.database.transaction() as connection:
            cursor = connection.execute(
                "INSERT INTO project_items(project_id, kind, status, title, content, file_path, "
                "created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (project_id, clean_kind, status[:40], clean_title, content.strip(), file_path, now, now),
            )
            item_id = int(cursor.lastrowid)
            connection.execute(
                "UPDATE projects SET last_activity = ?, updated_at = ? WHERE id = ?",
                (now, now, project_id),
            )
        return self.get_item(item_id)

    def get_item(self, item_id: int) -> dict[str, Any]:
        with self.database.connect() as connection:
            row = connection.execute("SELECT * FROM project_items WHERE id = ?", (item_id,)).fetchone()
        if row is None:
            raise KeyError(f"Project item {item_id} was not found")
        return dict(row)

    def items(self, project_id: int, limit: int = 250) -> list[dict[str, Any]]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM project_items WHERE project_id = ? ORDER BY updated_at DESC, id DESC LIMIT ?",
                (project_id, max(1, limit)),
            ).fetchall()
        return [dict(row) for row in rows]

    def update_item(self, item_id: int, *, status: str | None = None, content: str | None = None) -> dict[str, Any]:
        item = self.get_item(item_id)
        now = utc_now()
        with self.database.transaction() as connection:
            connection.execute(
                "UPDATE project_items SET status = ?, content = ?, updated_at = ? WHERE id = ?",
                (status or item["status"], item["content"] if content is None else content, now, item_id),
            )
            connection.execute(
                "UPDATE projects SET last_activity = ?, updated_at = ? WHERE id = ?",
                (now, now, int(item["project_id"])),
            )
        return self.get_item(item_id)

    def delete_item(self, item_id: int) -> bool:
        with self.database.transaction() as connection:
            cursor = connection.execute("DELETE FROM project_items WHERE id = ?", (item_id,))
            return cursor.rowcount > 0

    def set_active(self, project_id: int | None) -> None:
        if project_id is not None:
            self.get(project_id)
        self.settings.update(active_project_id=str(project_id or ""))

    def active_project_id(self) -> int | None:
        raw = self.settings.get().active_project_id
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return None
        return value if value > 0 else None

    def active(self) -> dict[str, Any] | None:
        project_id = self.active_project_id()
        if project_id is None:
            return None
        try:
            return self.get(project_id)
        except KeyError:
            self.set_active(None)
            return None

    def relevant(self, query: str, limit: int = 2) -> list[dict[str, Any]]:
        active = self.active()
        candidates = self.list(limit=100)
        tokens = Counter(TOKEN_RE.findall(query.lower()))
        scored: list[tuple[float, dict[str, Any]]] = []
        for project in candidates:
            haystack = f"{project['name']} {project['description']} {project['current_state']}"
            project_tokens = TOKEN_RE.findall(haystack.lower())
            overlap = sum(min(count, project_tokens.count(token)) for token, count in tokens.items())
            score = float(overlap * 4)
            if active and int(project["id"]) == int(active["id"]):
                score += 5
            if score > 0:
                scored.append((score, project))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [project for _, project in scored[: max(1, limit)]]

    def context(self, query: str) -> str:
        sections: list[str] = []
        for project in self.relevant(query, limit=2):
            items = self.items(int(project["id"]), limit=20)
            item_lines = [
                f"- [{item['kind']}/{item['status']}] {item['title']}: {item['content']}".rstrip(": ")
                for item in items[:12]
            ]
            sections.append(
                f"Project #{project['id']}: {project['name']} ({project['status']})\n"
                f"Description: {project['description'] or 'Not provided'}\n"
                f"Current state: {project['current_state'] or 'Not recorded'}\n"
                + ("Recent project records:\n" + "\n".join(item_lines) if item_lines else "")
            )
        return "\n\n".join(section.strip() for section in sections if section.strip())

    @staticmethod
    def _project(row: Any) -> dict[str, Any]:
        item = dict(row)
        try:
            item["important_files"] = json.loads(item.pop("important_files_json") or "[]")
        except (json.JSONDecodeError, TypeError):
            item.pop("important_files_json", None)
            item["important_files"] = []
        return item
