from __future__ import annotations

from typing import Any

from .database import Database
from .memory import MemoryDisabledError, MemoryService
from .personality import ANGEL_PERSONALITY, response_style_instruction
from .settings import SettingsService


class ContextBuilder:
    def __init__(
        self,
        database: Database,
        settings: SettingsService,
        memory: MemoryService,
        history_limit: int = 18,
        character_limit: int = 18_000,
    ) -> None:
        self.database = database
        self.settings = settings
        self.memory = memory
        self.history_limit = history_limit
        self.character_limit = character_limit

    def build(
        self,
        conversation_id: int,
        user_message: str,
        tool_results: list[str] | None = None,
        extra_system: str = "",
    ) -> list[dict[str, str]]:
        current = self.settings.get()
        location = current.location or "Not configured"
        system_parts = [
            ANGEL_PERSONALITY,
            response_style_instruction(current.response_style),
            "USER SETTINGS\n"
            f"Display name: {current.display_name or 'Not provided'}\n"
            f"Approximate location: {location}\n"
            f"Internet search: {'enabled' if current.internet_search_enabled else 'disabled'}\n"
            f"Memory: {'enabled' if current.memory_enabled else 'disabled'}",
        ]
        if current.memory_enabled:
            try:
                memories = self.memory.search(user_message, limit=6)
            except MemoryDisabledError:
                memories = []
            if memories:
                system_parts.append(
                    "RELEVANT SAVED MEMORIES\n"
                    + "\n".join(
                        f"- Memory #{item['id']} [{item['category']}]: {item['text']}"
                        for item in memories
                    )
                )
        if extra_system.strip():
            system_parts.append(extra_system.strip())
        if tool_results:
            system_parts.append(
                "TOOL RESULTS FOR THIS REQUEST\n"
                + "\n\n".join(result[:8_000] for result in tool_results)
            )

        messages: list[dict[str, str]] = [
            {"role": "system", "content": "\n\n".join(system_parts)}
        ]
        history = self.database.get_messages(conversation_id, limit=self.history_limit)
        # The current user turn is stored before context construction; include it exactly once.
        if history and history[-1]["role"] == "user" and history[-1]["content"] == user_message:
            history = history[:-1]
        for item in history:
            if item["role"] in {"user", "assistant"}:
                messages.append({"role": item["role"], "content": item["content"]})
        messages.append({"role": "user", "content": user_message})
        return self._trim(messages)

    def append_tool_exchange(
        self,
        messages: list[dict[str, str]],
        model_request: str,
        tool_result: str,
    ) -> list[dict[str, str]]:
        extended = list(messages)
        extended.append({"role": "assistant", "content": model_request})
        extended.append(
            {
                "role": "system",
                "content": "TOOL RESULT (real execution):\n" + tool_result,
            }
        )
        return self._trim(extended)

    def _trim(self, messages: list[dict[str, str]]) -> list[dict[str, str]]:
        if sum(len(message["content"]) for message in messages) <= self.character_limit:
            return messages
        system = messages[0]
        tail = messages[1:]
        kept: list[dict[str, str]] = []
        remaining = max(1_000, self.character_limit - len(system["content"]))
        for item in reversed(tail):
            if len(item["content"]) <= remaining or not kept:
                kept.append(item)
                remaining -= len(item["content"])
            else:
                break
        kept.reverse()
        return [system, *kept]
