from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Callable

from .context import ContextBuilder
from .database import Database
from .ollama_client import OllamaClient, OllamaError
from .recommendations import RecommendationService
from .settings import SettingsService
from .tools import (
    MalformedToolRequest,
    ToolLoop,
    ToolLoopLimitError,
    ToolRegistry,
    ToolRequest,
    ToolResult,
    UnknownToolError,
    parse_tool_request,
)


@dataclass(frozen=True)
class BrainResponse:
    content: str
    sources: list[dict[str, str]] = field(default_factory=list)
    tool_calls: int = 0
    local_ai_available: bool = True


class AngelBrain:
    def __init__(
        self,
        database: Database,
        settings: SettingsService,
        context: ContextBuilder,
        tools: ToolRegistry,
        ollama: OllamaClient,
        recommendations: RecommendationService,
        logger: logging.Logger | None = None,
        maximum_tool_calls: int = 3,
    ) -> None:
        self.database = database
        self.settings = settings
        self.context = context
        self.tools = tools
        self.ollama = ollama
        self.recommendations = recommendations
        self.logger = logger or logging.getLogger("angel.brain")
        self.maximum_tool_calls = maximum_tool_calls

    def respond(
        self,
        user_text: str,
        conversation_id: int,
        mode: str | None = None,
        status_callback: Callable[[str], None] | None = None,
    ) -> BrainResponse:
        if not self.database.conversation_exists(conversation_id):
            raise ValueError("Conversation does not exist")
        clean_user_text = user_text.strip()
        if not clean_user_text and not mode:
            raise ValueError("Message cannot be empty")
        self._note_recommendation_feedback(clean_user_text)

        display_text = clean_user_text
        effective_text = clean_user_text
        if mode:
            quick_prompt = self.recommendations.build_prompt(mode)
            effective_text = quick_prompt + (
                f"\nUser note: {clean_user_text}" if clean_user_text else ""
            )
            display_text = f"{mode}" + (f" — {clean_user_text}" if clean_user_text else "")

        self.database.add_message(conversation_id, "user", display_text)
        self._set_title_from_first_turn(conversation_id, display_text)
        current = self.settings.get()
        loop = ToolLoop(self.tools, self.maximum_tool_calls)
        sources: list[dict[str, str]] = []
        preflight_results: list[str] = []

        planned = self._planned_tool(clean_user_text, mode, current.location)
        if planned is not None:
            self._status(status_callback, f"Using {planned.name.replace('_', ' ')}…")
            result = loop.execute(planned)
            preflight_results.append(result.content)
            self._merge_sources(sources, result)

        messages = self.context.build(
            conversation_id,
            effective_text,
            tool_results=preflight_results,
            extra_system=(
                "This is an Angel quick action. Give a concrete, non-repetitive recommendation."
                if mode
                else ""
            ),
        )
        self._status(status_callback, "Thinking…")

        try:
            raw_response = self.ollama.chat(current.ollama_url, current.model, messages)
            while True:
                try:
                    request = parse_tool_request(raw_response)
                except MalformedToolRequest:
                    final = (
                        "I couldn't safely understand the tool request from the local model, so I did "
                        "not run anything. Please try phrasing that once more."
                    )
                    return self._finish(conversation_id, final, sources, loop.calls, True, mode)
                if request is None:
                    return self._finish(
                        conversation_id,
                        self._clean_response(raw_response),
                        sources,
                        loop.calls,
                        True,
                        mode,
                    )
                self._status(status_callback, f"Using {request.name.replace('_', ' ')}…")
                try:
                    result = loop.execute(request)
                except UnknownToolError:
                    final = (
                        f"The local model requested a tool named '{request.name}', but Angel rejected it "
                        "because it is not allowlisted. Nothing unsafe was run."
                    )
                    return self._finish(conversation_id, final, sources, loop.calls, True, mode)
                except ToolLoopLimitError:
                    final = (
                        "I stopped because the safe tool-call limit was reached. I won't keep looping or "
                        "pretend the request completed."
                    )
                    return self._finish(conversation_id, final, sources, loop.calls, True, mode)
                self._merge_sources(sources, result)
                messages = self.context.append_tool_exchange(messages, raw_response, result.content)
                self._status(status_callback, "Thinking with the tool result…")
                raw_response = self.ollama.chat(current.ollama_url, current.model, messages)
        except OllamaError as exc:
            self.logger.info("Local AI unavailable during response: %s", exc)
            final = self._offline_fallback(preflight_results, sources)
            return self._finish(conversation_id, final, sources, loop.calls, False, mode)
        except Exception:
            self.logger.exception("Unexpected Angel brain failure")
            final = "Something went wrong while I was thinking. Your conversation is still saved locally."
            return self._finish(conversation_id, final, sources, loop.calls, False, mode)

    def _finish(
        self,
        conversation_id: int,
        content: str,
        sources: list[dict[str, str]],
        tool_calls: int,
        local_ai_available: bool,
        mode: str | None,
    ) -> BrainResponse:
        clean_content = content.strip() or "I don't have a usable response yet."
        self.database.add_message(conversation_id, "assistant", clean_content, sources)
        if mode and clean_content and local_ai_available:
            self.recommendations.record(mode, clean_content)
        return BrainResponse(clean_content, list(sources), tool_calls, local_ai_available)

    @staticmethod
    def _clean_response(response: str) -> str:
        return response.replace("ANGEL_FINAL_RESPONSE", "").strip()

    @staticmethod
    def _merge_sources(target: list[dict[str, str]], result: ToolResult) -> None:
        existing = {source.get("url") for source in target}
        for source in result.sources:
            if source.get("url") not in existing:
                target.append(source)
                existing.add(source.get("url"))

    def _set_title_from_first_turn(self, conversation_id: int, text: str) -> None:
        messages = self.database.get_messages(conversation_id, limit=3)
        if len(messages) == 1:
            title = " ".join(text.split())[:55]
            self.database.rename_conversation(conversation_id, title or "New Conversation")

    def _planned_tool(
        self, text: str, mode: str | None, location: str
    ) -> ToolRequest | None:
        lowered = text.lower().strip()
        forget = re.search(r"\bforget\s+(?:memory\s*)?#?(\d+)\b", lowered)
        if forget:
            return ToolRequest("forget_memory", {"memory_id": int(forget.group(1))})

        remember = re.match(r"^(?:please\s+)?remember(?:\s+that)?\s+(.+)$", text, re.IGNORECASE)
        if remember:
            memory_text = remember.group(1).strip().rstrip(".")
            category = self._memory_category(memory_text)
            return ToolRequest("remember", {"text": memory_text, "category": category})
        dislike = re.match(r"^(?:please\s+)?(?:don't|do not) recommend\s+(.+?)\s+again[.!]?$", text, re.IGNORECASE)
        if dislike:
            return ToolRequest(
                "remember",
                {"text": f"Do not recommend {dislike.group(1).strip()} again.", "category": "dislike"},
            )

        if re.search(r"\bwhat (?:do you remember|have you remembered) about\b", lowered):
            return ToolRequest("search_memory", {"query": text, "limit": 6})
        if re.search(
            r"\b(what(?:'s| is) (?:the )?(?:local )?(?:date|time)|what day is it|today'?s date)\b",
            lowered,
        ):
            return ToolRequest("current_datetime", {})

        if not self.settings.get().internet_search_enabled:
            return None
        if mode in {"Get Me Out", "Something Free"} and not location:
            return None
        if mode in {"Make Money", "Get Me Out", "Something Free"}:
            query = self._quick_action_search_query(mode, location)
            return ToolRequest("search_web", {"query": query, "limit": 5})
        current_terms = re.search(
            r"\b(search(?: the web)?|look up|latest|current|today|tonight|news|weather|nearby|"
            r"open now|events?|hiring|job openings?|prices?)\b",
            lowered,
        )
        if current_terms:
            query = text
            if location and re.search(r"\b(nearby|local|near me|events?|hiring|open now)\b", lowered):
                query = f"{text} near {location}"
            return ToolRequest("search_web", {"query": query, "limit": 5})
        return None

    @staticmethod
    def _quick_action_search_query(mode: str, location: str) -> str:
        where = f" near {location}" if location else ""
        if mode == "Make Money":
            return f"legitimate jobs hiring and short paid opportunities{where} current"
        if mode == "Get Me Out":
            return f"parks libraries inexpensive events and things to do{where} today"
        return f"free events parks libraries and free activities{where} today"

    @staticmethod
    def _memory_category(text: str) -> str:
        lowered = text.lower()
        if any(word in lowered for word in ("don't like", "dislike", "hate", "avoid")):
            return "dislike"
        if any(word in lowered for word in ("prefer", "favorite", "like ")):
            return "preference"
        if any(word in lowered for word in ("project", "building", "working on")):
            return "project"
        if any(word in lowered for word in ("goal", "want to", "plan to")):
            return "goal"
        if any(word in lowered for word in ("every day", "every week", "routine")):
            return "routine"
        return "general"

    def _note_recommendation_feedback(self, text: str) -> None:
        lowered = text.lower().strip()
        if re.search(r"\b(i did it|done|finished|completed that)\b", lowered):
            self.recommendations.mark_latest("completed")
        elif re.search(r"\b(no thanks|not interested|bad suggestion|don't want that)\b", lowered):
            self.recommendations.mark_latest("rejected")

    @staticmethod
    def _offline_fallback(
        tool_results: list[str], sources: list[dict[str, str]]
    ) -> str:
        if tool_results:
            prefix = "The local AI is offline, but the safe tool completed:\n\n"
            if sources:
                return prefix + tool_results[-1] + "\n\nThe verified sources are listed below."
            return prefix + tool_results[-1]
        return (
            "Local AI is offline right now. Your conversation is saved, and Memory and Settings remain "
            "available. Start Ollama or use Settings → Recheck Connection, then try again."
        )

    @staticmethod
    def _status(callback: Callable[[str], None] | None, value: str) -> None:
        if callback:
            callback(value)
