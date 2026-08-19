from __future__ import annotations

import re

from ..brain import AngelBrain, ToolRequest
from .combined import asks_for_combined_current_info, weather_query


class WeatherBrain(AngelBrain):
    """AngelBrain extension for weather-aware current-information requests.

    The original AngelBrain remains the base reasoning engine. This subclass only
    changes preflight tool selection for combined weather/date-time questions.
    """

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
                or "search_web" not in self.tools.names
            ):
                return super()._planned_tool(
                    text, mode, location, connectivity_mode
                )

            return ToolRequest(
                "search_web",
                {"query": weather_query(text, location), "limit": 5},
            )

        return super()._planned_tool(text, mode, location, connectivity_mode)
