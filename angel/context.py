from __future__ import annotations

from typing import Any

from .attachments import attachment_context
from .database import Database
from .memory import MemoryDisabledError, MemoryService
from .personality import (
    ANGEL_BEHAVIOR,
    ANGEL_IDENTITY,
    ANGEL_TOOL_INSTRUCTIONS,
    ANGEL_TRUTHFULNESS,
    response_style_instruction,
)
from .projects import ProjectService
from .knowledge import KnowledgeService
from .settings import SettingsService


class ContextBuilder:
    def __init__(
        self,
        database: Database,
        settings: SettingsService,
        memory: MemoryService,
        history_limit: int = 18,
        character_limit: int = 18_000,
        projects: ProjectService | None = None,
        knowledge: KnowledgeService | None = None,
    ) -> None:
        self.database = database
        self.settings = settings
        self.memory = memory
        self.history_limit = history_limit
        self.character_limit = character_limit
        self.projects = projects
        self.knowledge = knowledge

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
            ANGEL_IDENTITY,
            ANGEL_BEHAVIOR,
            ANGEL_TRUTHFULNESS,
            response_style_instruction(current.response_style),
            "ACTIVE USER PROFILE\n"
            f"Display name: {current.display_name or 'Not provided'}\n"
            f"Approximate location: {location}\n"
            f"Technical explanation preference: {current.technical_level}\n"
            f"Formatting preference: {current.formatting_preference}\n"
            f"Workflow preferences: {current.workflow_preferences or 'None recorded'}\n"
            f"Connectivity mode: {current.connectivity_mode}\n"
            f"Memory: {'enabled' if current.memory_enabled else 'disabled'}",
        ]
        if self.projects is not None:
            project_context = self.projects.context(user_message)
            if project_context:
                system_parts.append(
                    "ACTIVE / RELEVANT PROJECT CONTEXT\nUse this naturally; do not announce the project database.\n"
                    + project_context
                )
        if current.memory_enabled:
            try:
                memories = self.memory.search(user_message, limit=6)
            except MemoryDisabledError:
                memories = []
            if memories:
                system_parts.append(
                    "RELEVANT LONG-TERM MEMORIES\nUse these naturally without saying 'according to memory'.\n"
                    + "\n".join(
                        f"- [{item['category']}; importance {item.get('importance', 3)}/5] "
                        f"{item.get('title') + ': ' if item.get('title') else ''}{item['text']}"
                        for item in memories
                    )
                )
        if self.knowledge is not None and current.knowledge_enabled:
            knowledge_context = self.knowledge.context(user_message, limit=4)
            if knowledge_context:
                system_parts.append(
                    "RELEVANT LOCAL KNOWLEDGE\nThis text was actually indexed locally. Cite the document title when useful.\n"
                    + knowledge_context
                )
        summary = self._conversation_summary(conversation_id)
        if summary:
            system_parts.append("EARLIER CONVERSATION SUMMARY\n" + summary)
        if extra_system.strip():
            system_parts.append(extra_system.strip())
        if tool_results:
            system_parts.append(
                "TOOL RESULTS FOR THIS REQUEST\n"
                + "\n\n".join(result[:8_000] for result in tool_results)
            )
        system_parts.append(ANGEL_TOOL_INSTRUCTIONS)

        messages: list[dict[str, str]] = [
            {"role": "system", "content": "\n\n".join(system_parts)}
        ]
        history = self.database.get_messages(conversation_id, limit=self.history_limit)
        # The current user turn is stored before context construction; include it exactly once.
        if history and history[-1]["role"] == "user" and history[-1]["content"] == user_message:
            history = history[:-1]
        for item in history:
            if item["role"] in {"user", "assistant"}:
                content = item["content"]
                if item["role"] == "user" and item.get("attachments"):
                    content += "\n\n" + attachment_context(item["attachments"])
                messages.append({"role": item["role"], "content": content})
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
        profile = self.settings.get().resource_profile
        profile_limit = {
            "Low Resource": min(self.character_limit, 12_000),
            "Balanced": max(self.character_limit, 24_000),
            "Maximum Quality": max(self.character_limit, 40_000),
        }.get(profile, self.character_limit)
        if sum(len(message["content"]) for message in messages) <= profile_limit:
            return messages
        system = messages[0]
        tail = messages[1:]
        kept: list[dict[str, str]] = []
        remaining = max(1_000, profile_limit - len(system["content"]))
        for item in reversed(tail):
            if len(item["content"]) <= remaining or not kept:
                kept.append(item)
                remaining -= len(item["content"])
            else:
                break
        kept.reverse()
        return [system, *kept]

    def _conversation_summary(self, conversation_id: int) -> str:
        history = self.database.get_messages(conversation_id, limit=200)
        if len(history) <= self.history_limit:
            saved = self.database.get_conversation_summary(conversation_id)
            return str(saved["summary"]) if saved else ""
        older = history[: -self.history_limit]
        through_id = int(older[-1]["id"])
        existing = self.database.get_conversation_summary(conversation_id)
        if existing and int(existing["through_message_id"]) >= through_id:
            return str(existing["summary"])
        lines: list[str] = []
        for message in older[-40:]:
            role = "User" if message["role"] == "user" else "Angel"
            compact = " ".join(str(message["content"]).split())
            if compact:
                lines.append(f"{role}: {compact[:240]}")
        summary = "\n".join(lines)[-5_000:]
        if summary:
            self.database.set_conversation_summary(conversation_id, through_id, summary)
        return summary
