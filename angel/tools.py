from __future__ import annotations

import inspect
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

from .database import Database
from .memory import MemoryDisabledError, MemoryService
from .search import SearchService, SearchUnavailableError
from .settings import SettingsService


TOOL_MARKER = "ANGEL_TOOL_REQUEST"


class MalformedToolRequest(ValueError):
    pass


class UnknownToolError(ValueError):
    pass


class ToolExecutionError(RuntimeError):
    pass


class ToolLoopLimitError(RuntimeError):
    pass


@dataclass(frozen=True)
class ToolRequest:
    name: str
    arguments: dict[str, Any]


@dataclass
class ToolResult:
    name: str
    success: bool
    content: str
    data: Any = None
    sources: list[dict[str, str]] = field(default_factory=list)


def parse_tool_request(text: str) -> ToolRequest | None:
    """Parse the single strict JSON tool envelope used with small local models."""
    marker_index = text.find(TOOL_MARKER)
    if marker_index < 0:
        return None
    payload = text[marker_index + len(TOOL_MARKER) :].strip()
    payload = re.sub(r"^```(?:json)?\s*", "", payload, flags=re.IGNORECASE)
    payload = re.sub(r"\s*```\s*$", "", payload)
    decoder = json.JSONDecoder()
    try:
        parsed, _ = decoder.raw_decode(payload)
    except (json.JSONDecodeError, TypeError) as exc:
        raise MalformedToolRequest("Tool request must contain valid JSON") from exc
    if not isinstance(parsed, dict):
        raise MalformedToolRequest("Tool request must be a JSON object")
    name = parsed.get("name")
    arguments = parsed.get("arguments", {})
    if not isinstance(name, str) or not name.strip():
        raise MalformedToolRequest("Tool request is missing a name")
    if not isinstance(arguments, dict):
        raise MalformedToolRequest("Tool arguments must be a JSON object")
    return ToolRequest(name=name.strip(), arguments=arguments)


class ToolRegistry:
    def __init__(self, database: Database, logger: logging.Logger | None = None) -> None:
        self.database = database
        self.logger = logger or logging.getLogger("angel.tools")
        self._tools: dict[str, Callable[..., ToolResult]] = {}

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._tools))

    def register(self, name: str, handler: Callable[..., ToolResult]) -> None:
        clean_name = name.strip()
        if not re.fullmatch(r"[a-z][a-z0-9_]*", clean_name):
            raise ValueError("Tool name must be a lowercase identifier")
        self._tools[clean_name] = handler

    def execute(self, request: ToolRequest) -> ToolResult:
        handler = self._tools.get(request.name)
        if handler is None:
            self.database.add_tool_activity(request.name, False, "unknown tool rejected")
            raise UnknownToolError(f"Tool '{request.name}' is not allowed")
        try:
            signature = inspect.signature(handler)
            signature.bind(**request.arguments)
            result = handler(**request.arguments)
            if not isinstance(result, ToolResult):
                raise ToolExecutionError("Tool returned an invalid result")
            self.database.add_tool_activity(request.name, result.success, result.content)
            return result
        except TypeError as exc:
            self.database.add_tool_activity(request.name, False, "invalid arguments")
            raise ToolExecutionError(f"Invalid arguments for {request.name}") from exc
        except (MemoryDisabledError, SearchUnavailableError, ValueError, KeyError) as exc:
            self.database.add_tool_activity(request.name, False, str(exc))
            return ToolResult(request.name, False, str(exc))
        except Exception as exc:
            self.database.add_tool_activity(request.name, False, type(exc).__name__)
            self.logger.exception("Tool %s failed", request.name)
            return ToolResult(request.name, False, f"{request.name} failed safely")


def create_tool_registry(
    database: Database,
    settings: SettingsService,
    memory: MemoryService,
    search: SearchService,
    logger: logging.Logger | None = None,
) -> ToolRegistry:
    registry = ToolRegistry(database, logger)

    def search_web(query: str, limit: int = 5) -> ToolResult:
        if not settings.get().internet_search_enabled:
            return ToolResult("search_web", False, "Internet search is disabled in Angel Settings")
        results = search.search(str(query), int(limit))
        sources = [result.as_dict() for result in results]
        lines = [
            f"{index}. {item.title}\nURL: {item.url}\nSnippet: {item.snippet}"
            for index, item in enumerate(results, 1)
        ]
        return ToolResult(
            "search_web",
            True,
            "Searched the web successfully.\n" + "\n\n".join(lines),
            data=sources,
            sources=sources,
        )

    def remember(text: str, category: str = "general") -> ToolResult:
        item = memory.add(str(text), str(category))
        return ToolResult(
            "remember",
            True,
            f"Saved memory #{item['id']} in {item['category']}: {item['text']}",
            data=item,
        )

    def search_memory(query: str, limit: int = 6) -> ToolResult:
        items = memory.search(str(query), int(limit))
        if not items:
            return ToolResult("search_memory", True, "No matching saved memories were found", data=[])
        content = "Matching saved memories:\n" + "\n".join(
            f"#{item['id']} [{item['category']}] {item['text']}" for item in items
        )
        return ToolResult("search_memory", True, content, data=items)

    def forget_memory(memory_id: int) -> ToolResult:
        deleted = memory.delete(int(memory_id))
        if deleted:
            return ToolResult("forget_memory", True, f"Deleted memory #{int(memory_id)}")
        return ToolResult("forget_memory", False, f"Memory #{int(memory_id)} was not found")

    def current_datetime() -> ToolResult:
        now = datetime.now().astimezone()
        timezone_name = now.tzname() or str(now.tzinfo or "local time")
        data = {
            "iso": now.isoformat(timespec="seconds"),
            "date": now.strftime("%A, %B %d, %Y"),
            "time": now.strftime("%I:%M:%S %p").lstrip("0"),
            "timezone": timezone_name,
        }
        return ToolResult(
            "current_datetime",
            True,
            f"Local date: {data['date']}\nLocal time: {data['time']}\nTimezone: {timezone_name}",
            data=data,
        )

    registry.register("search_web", search_web)
    registry.register("remember", remember)
    registry.register("search_memory", search_memory)
    registry.register("forget_memory", forget_memory)
    registry.register("current_datetime", current_datetime)
    return registry


class ToolLoop:
    """Small reusable guard that prevents unbounded model-requested tool loops."""

    def __init__(self, registry: ToolRegistry, maximum: int = 3) -> None:
        self.registry = registry
        self.maximum = maximum
        self.calls = 0

    def execute(self, request: ToolRequest) -> ToolResult:
        if self.calls >= self.maximum:
            raise ToolLoopLimitError(f"Tool call limit of {self.maximum} reached")
        self.calls += 1
        return self.registry.execute(request)
