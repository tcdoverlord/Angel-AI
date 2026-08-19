from __future__ import annotations

import re

from ..tools import ToolRequest


class DateTimeNeuron:
    """Recognizes date/time requests without asking the language model for reality."""

    name = "datetime"

    _patterns = (
        re.compile(r"\bwhat\s+(?:the\s+)?(?:local\s+)?(?:date|time)\s+is\s+it\b"),
        re.compile(
            r"\bwhat\s+(?:the\s+)?(?:date|time)\s+and\s+(?:the\s+)?(?:date|time)\s+is\s+it\b"
        ),
        re.compile(
            r"\bwhat\s+is\s+(?:the\s+)?(?:current\s+|local\s+)?"
            r"(?:date|time)(?:\s+and\s+(?:the\s+)?(?:current\s+|local\s+)?"
            r"(?:date|time))?\b"
        ),
        re.compile(
            r"\b(?:tell me|give me|show me)\s+(?:the\s+)?"
            r"(?:current\s+|local\s+)?(?:date|time)"
            r"(?:\s+and\s+(?:the\s+)?(?:current\s+|local\s+)?"
            r"(?:date|time))?\b"
        ),
        re.compile(r"\bwhat day is it\b"),
        re.compile(r"\btoday'?s date\b"),
    )

    def can_handle(self, text: str) -> bool:
        lowered = " ".join(text.lower().split()).strip()
        return any(pattern.search(lowered) for pattern in self._patterns)

    def activate(self) -> ToolRequest:
        """Request the existing verified datetime capability."""
        return ToolRequest("current_datetime", {})
