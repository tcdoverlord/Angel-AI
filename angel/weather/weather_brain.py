from __future__ import annotations

import re

from ..brain import AngelBrain, ToolRequest
from .combined import asks_for_combined_current_info, asks_for_date_time, asks_for_weather


class WeatherBrain(AngelBrain):
    """Routes live date/time and weather requests to verified local capabilities.

    The base AngelBrain remains responsible for normal conversation and the
    existing tool loop. This layer prevents live weather/date-time requests from
    being handed to a generic web-search path.
    """

    @staticmethod
    def _weather_location(text: str, configured_location: str) -> str:
        match = re.search(
            r"\b(?:weather|forecast|temperature|conditions)\b"
            r"(?:\s+(?:in|for|near)\s+)([^?.!;]+)",
            text,
            re.IGNORECASE,
        )
        if match:
            candidate = " ".join(match.group(1).split()).strip()
            # Avoid turning conversational trailing words into a location.
            candidate = re.sub(
                r"\s+(?:right now|today|tomorrow|please|now)$", "", candidate, flags=re.I
            ).strip()
            if candidate:
                return candidate
        return configured_location

    def _planned_tool(
        self,
        text: str,
        mode: str | None,
        location: str,
        connectivity_mode: str,
    ) -> ToolRequest | None:
        if asks_for_combined_current_info(text):
            if (
                connectivity_mode == "Offline"
                or not self.settings.get().internet_search_enabled
                or "current_weather" not in self.tools.names
            ):
                return ToolRequest("current_datetime", {})
            return ToolRequest(
                "current_weather",
                {"location": self._weather_location(text, location)},
            )

        if asks_for_weather(text):
            if (
                connectivity_mode == "Offline"
                or not self.settings.get().internet_search_enabled
                or "current_weather" not in self.tools.names
            ):
                return None
            return ToolRequest(
                "current_weather",
                {"location": self._weather_location(text, location)},
            )

        if asks_for_date_time(text):
            return ToolRequest("current_datetime", {})

        return super()._planned_tool(text, mode, location, connectivity_mode)
