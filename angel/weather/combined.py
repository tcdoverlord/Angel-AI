from __future__ import annotations

import re


_DATE_TIME_PATTERN = re.compile(
    r"\b(?:what(?:'s| is)|tell me|give me|show me)?\s*"
    r"(?:the\s+)?(?:local\s+)?(?:date|time)|"
    r"\bwhat day is it\b|\btoday'?s date\b",
    re.IGNORECASE,
)

_WEATHER_PATTERN = re.compile(
    r"\bweather\b|\bforecast\b|\btemperature\b|\bconditions\b",
    re.IGNORECASE,
)


def asks_for_date_time(text: str) -> bool:
    return bool(_DATE_TIME_PATTERN.search(text))


def asks_for_weather(text: str) -> bool:
    return bool(_WEATHER_PATTERN.search(text))


def asks_for_combined_current_info(text: str) -> bool:
    return asks_for_date_time(text) and asks_for_weather(text)


def weather_query(text: str, location: str) -> str:
    cleaned = text.strip()
    if location:
        return f"{cleaned}\nProvide current weather for {location}."
    return cleaned
