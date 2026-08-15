from __future__ import annotations

from typing import Any

from .database import Database, utc_now
from .settings import SettingsService


QUICK_ACTIONS: dict[str, dict[str, str]] = {
    "One More Thing": {
        "goal": "Decide what I should do next.",
        "guidance": (
            "Use what you already know about my time, energy, cost constraints, desire to leave home, "
            "projects, preferences, location, and recent suggestions. Recommend one to three strong, "
            "specific actions. Ask one short question only if essential."
        ),
    },
    "Make Money": {
        "goal": "Help me take a realistic next step toward earning money.",
        "guidance": (
            "Consider items to sell, a listing to create, a job application, verified local hiring, "
            "legitimate gigs, portfolio work, or a small freelance action. Search before naming current "
            "jobs, openings, prices, or opportunities. Never promise income."
        ),
    },
    "Get Me Out": {
        "goal": "Help me get out of the house with a good nearby option.",
        "guidance": (
            "Use my configured approximate location and preferences. Consider parks, libraries, public "
            "spaces, trails, markets, and community activities. Search before claiming anything current, "
            "nearby, open, or scheduled."
        ),
    },
    "Build Something": {
        "goal": "Give me a satisfying small thing to build next.",
        "guidance": (
            "Fit it to 15 minutes, 30 minutes, one hour, or one evening. Reuse remembered projects when "
            "helpful. Avoid defaulting to enormous software products."
        ),
    },
    "Something Free": {
        "goal": "Give me a genuinely free worthwhile thing to do.",
        "guidance": (
            "Prioritize free parks, libraries, events, public spaces, learning, creativity, exercise, or "
            "home projects using resources I already have. Search before claiming a current local event."
        ),
    },
    "Surprise Me": {
        "goal": "Surprise me with a thoughtful next action that fits me.",
        "guidance": (
            "Use memory, current conversation, available time, location when useful, and recent suggestion "
            "history. Do not choose a random canned phrase."
        ),
    },
}


class RecommendationService:
    def __init__(self, database: Database, settings: SettingsService) -> None:
        self.database = database
        self.settings = settings

    def build_prompt(self, mode: str) -> str:
        if mode not in QUICK_ACTIONS:
            raise ValueError(f"Unknown quick action: {mode}")
        definition = QUICK_ACTIONS[mode]
        current = self.settings.get()
        location_line = current.location or "no location configured"
        recent = self.recent(limit=8)
        recent_text = "\n".join(
            f"- [{item['status']}] {item['mode']}: {item['suggestion'][:240]}" for item in recent
        ) or "- None yet"
        return (
            f"ANGEL QUICK ACTION: {mode}\n"
            f"Goal: {definition['goal']}\n"
            f"Guidance: {definition['guidance']}\n"
            f"Approximate location: {location_line}.\n"
            "Recent suggestions (avoid repeating rejected, completed, or very recent ideas):\n"
            f"{recent_text}\n"
            "Respond as the same Angel assistant in this conversation."
        )

    def record(self, mode: str, suggestion: str, status: str = "suggested") -> int:
        if mode not in QUICK_ACTIONS:
            raise ValueError(f"Unknown quick action: {mode}")
        if status not in {"suggested", "completed", "rejected"}:
            raise ValueError("Unsupported suggestion status")
        clean = " ".join(suggestion.split()).strip()[:2_000]
        if not clean:
            raise ValueError("Suggestion cannot be empty")
        now = utc_now()
        with self.database.transaction() as connection:
            cursor = connection.execute(
                "INSERT INTO recommendation_history(mode, suggestion, status, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (mode, clean, status, now, now),
            )
            return int(cursor.lastrowid)

    def recent(self, limit: int = 12) -> list[dict[str, Any]]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT id, mode, suggestion, status, created_at, updated_at "
                "FROM recommendation_history ORDER BY id DESC LIMIT ?",
                (max(1, limit),),
            ).fetchall()
        return [dict(row) for row in rows]

    def mark_latest(self, status: str) -> bool:
        if status not in {"completed", "rejected"}:
            raise ValueError("Unsupported suggestion status")
        with self.database.transaction() as connection:
            row = connection.execute(
                "SELECT id FROM recommendation_history ORDER BY id DESC LIMIT 1"
            ).fetchone()
            if row is None:
                return False
            connection.execute(
                "UPDATE recommendation_history SET status = ?, updated_at = ? WHERE id = ?",
                (status, utc_now(), int(row["id"])),
            )
            return True
