from __future__ import annotations

import pytest

from angel.search import SearchResult, SearchService
from angel.tools import (
    MalformedToolRequest,
    ToolLoop,
    ToolLoopLimitError,
    ToolRequest,
    UnknownToolError,
    create_tool_registry,
    parse_tool_request,
)


class Provider:
    def search(self, query, limit=5):
        return [
            SearchResult(
                "A real result", "https://example.com/result", "example.com", f"About {query}"
            )
        ]


def make_registry(services):
    database, settings, memory = services
    return create_tool_registry(database, settings, memory, SearchService(Provider()))


def test_allowlisted_tool_is_accepted(services):
    registry = make_registry(services)
    result = registry.execute(ToolRequest("current_datetime", {}))
    assert result.success is True
    assert "Local date:" in result.content


def test_unknown_tool_is_rejected(services):
    registry = make_registry(services)
    with pytest.raises(UnknownToolError):
        registry.execute(ToolRequest("run_powershell", {"command": "whoami"}))


@pytest.mark.parametrize(
    "text",
    [
        'ANGEL_TOOL_REQUEST {not-json}',
        'ANGEL_TOOL_REQUEST ["search_web"]',
        'ANGEL_TOOL_REQUEST {"arguments":{}}',
        'ANGEL_TOOL_REQUEST {"name":"search_web","arguments":[]}',
    ],
)
def test_malformed_tool_request_is_rejected(text):
    with pytest.raises(MalformedToolRequest):
        parse_tool_request(text)


def test_valid_tool_request_parser():
    request = parse_tool_request(
        'ANGEL_TOOL_REQUEST {"name":"search_memory","arguments":{"query":"purple"}}'
    )
    assert request == ToolRequest("search_memory", {"query": "purple"})
    assert parse_tool_request("No tool is needed.") is None


def test_tool_loop_maximum_is_enforced(services):
    loop = ToolLoop(make_registry(services), maximum=3)
    for _ in range(3):
        assert loop.execute(ToolRequest("current_datetime", {})).success
    with pytest.raises(ToolLoopLimitError):
        loop.execute(ToolRequest("current_datetime", {}))


def test_search_tool_respects_disabled_setting(services):
    _database, settings, _memory = services
    settings.update(internet_search_enabled=False)
    result = make_registry(services).execute(
        ToolRequest("search_web", {"query": "current news"})
    )
    assert result.success is False
    assert "disabled" in result.content.lower()
