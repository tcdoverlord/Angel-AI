from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from typing import Any


class WeatherUnavailableError(RuntimeError):
    """Raised when live weather cannot be obtained safely."""


@dataclass(frozen=True)
class WeatherSnapshot:
    location: str
    timezone: str
    observed_at: str
    temperature_f: float
    apparent_temperature_f: float
    humidity_percent: float
    precipitation_mm: float
    wind_mph: float
    condition: str
    latitude: float
    longitude: float

    def as_dict(self) -> dict[str, Any]:
        try:
            observed = datetime.fromisoformat(self.observed_at)
            date_text = observed.strftime("%A, %B %d, %Y")
            time_text = observed.strftime("%I:%M %p").lstrip("0")
        except ValueError:
            date_text = self.observed_at
            time_text = self.observed_at
        return {
            "location": self.location,
            "timezone": self.timezone,
            "observed_at": self.observed_at,
            "date": date_text,
            "time": time_text,
            "temperature_f": self.temperature_f,
            "apparent_temperature_f": self.apparent_temperature_f,
            "humidity_percent": self.humidity_percent,
            "precipitation_mm": self.precipitation_mm,
            "wind_mph": self.wind_mph,
            "condition": self.condition,
            "latitude": self.latitude,
            "longitude": self.longitude,
        }


_WEATHER_CODES = {
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
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
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


def _get_json(url: str, timeout: float = 8.0) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Angel Local Personal AI/1.2",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read(1_500_000).decode("utf-8"))
    except Exception as exc:
        raise WeatherUnavailableError("Live weather service is unavailable") from exc


def _geocode(location: str) -> tuple[str, float, float]:
    clean = " ".join(location.split()).strip()
    if not clean:
        raise WeatherUnavailableError(
            "No weather location is configured. Set Angel's city/region or name a location."
        )
    params = urllib.parse.urlencode(
        {"name": clean, "count": 1, "language": "en", "format": "json"}
    )
    payload = _get_json(f"https://geocoding-api.open-meteo.com/v1/search?{params}")
    results = payload.get("results") or []
    if not results:
        raise WeatherUnavailableError(f"I couldn't find a weather location for '{clean}'.")
    item = results[0]
    name = str(item.get("name") or clean)
    admin = str(item.get("admin1") or "").strip()
    country = str(item.get("country") or "").strip()
    label = ", ".join(part for part in (name, admin, country) if part)
    return label, float(item["latitude"]), float(item["longitude"])


def get_current_weather(location: str) -> WeatherSnapshot:
    label, latitude, longitude = _geocode(location)
    params = urllib.parse.urlencode(
        {
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "temperature_2m,relative_humidity_2m,apparent_temperature,"
                "precipitation,weather_code,wind_speed_10m"
            ),
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "timezone": "auto",
        }
    )
    payload = _get_json(f"https://api.open-meteo.com/v1/forecast?{params}")
    current = payload.get("current") or {}
    units = payload.get("current_units") or {}
    if "time" not in current or "temperature_2m" not in current:
        raise WeatherUnavailableError("Live weather returned incomplete current conditions.")

    code = int(current.get("weather_code", -1))
    return WeatherSnapshot(
        location=label,
        timezone=str(payload.get("timezone") or "local time"),
        observed_at=str(current["time"]),
        temperature_f=float(current["temperature_2m"]),
        apparent_temperature_f=float(current.get("apparent_temperature", current["temperature_2m"])),
        humidity_percent=float(current.get("relative_humidity_2m", 0)),
        precipitation_mm=float(current.get("precipitation", 0)),
        wind_mph=float(current.get("wind_speed_10m", 0)),
        condition=_WEATHER_CODES.get(code, f"Weather code {code}"),
        latitude=latitude,
        longitude=longitude,
    )
