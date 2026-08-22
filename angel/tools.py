from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import quote
from urllib.request import urlopen


@dataclass
class ToolResult:
    name: str
    content: str
    success: bool = True


def current_datetime() -> ToolResult:
    """Return the current local date, time, and timezone."""

    now = datetime.now().astimezone()

    return ToolResult(
        name="current_datetime",
        content=(
            f"Local date: {now:%A, %B %d, %Y}\n"
            f"Local time: {now:%I:%M:%S %p}\n"
            f"Timezone: {now.tzname() or now.tzinfo}"
        ),
    )


def weather(location: str) -> ToolResult:
    """Return current weather for a named location using Open-Meteo."""

    location = " ".join((location or "").split()).strip()

    if not location:
        return ToolResult(
            name="current_weather",
            content="Weather unavailable: no location was provided.",
            success=False,
        )

    try:
        geocode_url = (
            "https://geocoding-api.open-meteo.com/v1/search"
            f"?name={quote(location)}"
            "&count=1"
            "&language=en"
            "&format=json"
        )

        with urlopen(geocode_url, timeout=12) as response:
            geocoding = json.loads(response.read())

        results = geocoding.get("results") or []

        if not results:
            return ToolResult(
                name="current_weather",
                content=f"Location not found: {location}",
                success=False,
            )

        place = results[0]
        latitude = place["latitude"]
        longitude = place["longitude"]

        forecast_url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={latitude}"
            f"&longitude={longitude}"
            "&current="
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "weather_code,"
            "wind_speed_10m"
            "&temperature_unit=fahrenheit"
            "&wind_speed_unit=mph"
            "&timezone=auto"
        )

        with urlopen(forecast_url, timeout=12) as response:
            forecast = json.loads(response.read())

        current = forecast.get("current")

        if not current:
            return ToolResult(
                name="current_weather",
                content=f"Weather data unavailable for {location}.",
                success=False,
            )

        weather_code = current.get("weather_code")

        descriptions = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            56: "Light freezing drizzle",
            57: "Dense freezing drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            66: "Light freezing rain",
            67: "Heavy freezing rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            77: "Snow grains",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            85: "Slight snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail",
        }

        description = descriptions.get(
            weather_code,
            f"Weather code {weather_code}",
        )

        place_name = place.get("name") or location
        region = place.get("admin1")

        display_location = (
            f"{place_name}, {region}"
            if region
            else place_name
        )

        temperature = current.get("temperature_2m")
        apparent_temperature = current.get("apparent_temperature")
        humidity = current.get("relative_humidity_2m")
        wind_speed = current.get("wind_speed_10m")

        content = (
            f"Weather for {display_location}: {description}\n"
            f"Temperature: {temperature}°F "
            f"(feels like {apparent_temperature}°F)\n"
            f"Humidity: {humidity}%\n"
            f"Wind: {wind_speed} mph"
        )

        return ToolResult(
            name="current_weather",
            content=content,
            success=True,
        )

    except Exception as exc:
        return ToolResult(
            name="current_weather",
            content=f"Weather unavailable: {exc}",
            success=False,
        )


def looks_weather(text: str) -> bool:
    """Return True when text appears to request weather information."""

    return bool(
        re.search(
            r"\b(weather|forecast|temperature|conditions)\b",
            text or "",
            re.IGNORECASE,
        )
    )


def looks_datetime(text: str) -> bool:
    """Return True when text appears to request date/time information."""

    return bool(
        re.search(
            r"\b(date|time|today|what day)\b",
            text or "",
            re.IGNORECASE,
        )
    )