from __future__ import annotations

import re

from ..brain import AngelBrain, ToolRequest
from .combined import (
    asks_for_combined_current_info,
    asks_for_date_time,
    asks_for_weather,
)


class WeatherBrain(AngelBrain):
    """Routes live date/time and weather requests to verified capabilities.

    Combined requests use the enhanced multi-tool planner so Angel can obtain
    both the local date/time and current weather in one deterministic
    preflight pass.

    The legacy _planned_tool() interface remains compatible with the existing
    AngelBrain and test suite. For a combined request it returns the weather
    capability when available, matching the established compatibility contract.
    """

    @staticmethod
    def _weather_location(
        text: str,
        configured_location: str,
    ) -> str:
        """Extract an explicit weather location or use the configured location."""

        match = re.search(
            r"\b(?:weather|forecast|temperature|conditions)\b"
            r"(?:\s+(?:in|for|near)\s+)([^?.!;]+)",
            text,
            re.IGNORECASE,
        )

        if match:
            candidate = " ".join(
                match.group(1).split()
            ).strip()

            # Remove common conversational endings that are not part of the
            # requested location.
            candidate = re.sub(
                r"\s+(?:right now|today|tomorrow|please|now)$",
                "",
                candidate,
                flags=re.IGNORECASE,
            ).strip()

            if candidate:
                return candidate

        return configured_location

    def _planned_tools(
        self,
        text: str,
        mode: str | None,
        location: str,
        connectivity_mode: str,
    ) -> list[ToolRequest]:
        """Plan deterministic capabilities for the current-information request.

        Combined requests deliberately produce two independent capability
        requests:

        1. current_datetime
        2. current_weather, when internet weather access is available

        This prevents the local model from having to invent, select, or
        repeatedly request either live capability.
        """

        if asks_for_combined_current_info(text):
            planned: list[ToolRequest] = [
                ToolRequest(
                    "current_datetime",
                    {},
                )
            ]

            weather_available = (
                connectivity_mode != "Offline"
                and self.settings.get().internet_search_enabled
                and "current_weather" in self.tools.names
            )

            if weather_available:
                planned.append(
                    ToolRequest(
                        "current_weather",
                        {
                            "location": self._weather_location(
                                text,
                                location,
                            )
                        },
                    )
                )

            return planned

        if asks_for_weather(text):
            weather_available = (
                connectivity_mode != "Offline"
                and self.settings.get().internet_search_enabled
                and "current_weather" in self.tools.names
            )

            if not weather_available:
                return []

            return [
                ToolRequest(
                    "current_weather",
                    {
                        "location": self._weather_location(
                            text,
                            location,
                        )
                    },
                )
            ]

        if asks_for_date_time(text):
            return [
                ToolRequest(
                    "current_datetime",
                    {},
                )
            ]

        # Preserve the existing AngelBrain planning behavior for everything
        # outside the dedicated live-information capability family.
        planned = self._planned_tool(
            text,
            mode,
            location,
            connectivity_mode,
        )

        return [planned] if planned is not None else []

    def _planned_tool(
        self,
        text: str,
        mode: str | None,
        location: str,
        connectivity_mode: str,
    ) -> ToolRequest | None:
        """Provide the legacy single-tool planning contract.

        _planned_tools() is the preferred path for actual combined execution.
        This method intentionally remains single-tool compatible because the
        existing AngelBrain/test contract expects a ToolRequest here.

        For a combined request, current_weather is returned when available.
        If weather is unavailable, current_datetime remains available locally.
        """

        if asks_for_combined_current_info(text):
            weather_available = (
                connectivity_mode != "Offline"
                and self.settings.get().internet_search_enabled
                and "current_weather" in self.tools.names
            )

            if weather_available:
                return ToolRequest(
                    "current_weather",
                    {
                        "location": self._weather_location(
                            text,
                            location,
                        )
                    },
                )

            return ToolRequest(
                "current_datetime",
                {},
            )

        if asks_for_weather(text):
            weather_available = (
                connectivity_mode != "Offline"
                and self.settings.get().internet_search_enabled
                and "current_weather" in self.tools.names
            )

            if not weather_available:
                return None

            return ToolRequest(
                "current_weather",
                {
                    "location": self._weather_location(
                        text,
                        location,
                    )
                },
            )

        if asks_for_date_time(text):
            return ToolRequest(
                "current_datetime",
                {},
            )

        return super()._planned_tool(
            text,
            mode,
            location,
            connectivity_mode,
        )