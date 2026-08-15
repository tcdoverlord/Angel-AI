from __future__ import annotations

from dataclasses import dataclass

from .database import Database


DEFAULT_SETTINGS: dict[str, str] = {
    "ollama_url": "http://127.0.0.1:11434",
    "model": "llama3.2:3b",
    "display_name": "",
    "city": "",
    "region": "",
    "postal_code": "",
    "response_style": "Balanced",
    "internet_search_enabled": "true",
    "memory_enabled": "true",
    "read_aloud_enabled": "true",
    "voice_name": "",
    "speech_rate": "0",
}


@dataclass(frozen=True)
class AngelSettings:
    ollama_url: str
    model: str
    display_name: str
    city: str
    region: str
    postal_code: str
    response_style: str
    internet_search_enabled: bool
    memory_enabled: bool
    read_aloud_enabled: bool
    voice_name: str
    speech_rate: int

    @property
    def location(self) -> str:
        return ", ".join(
            part for part in (self.city, self.region, self.postal_code) if part.strip()
        )


class SettingsService:
    def __init__(self, database: Database) -> None:
        self.database = database
        if not self.database.setting_values():
            self.database.set_settings(DEFAULT_SETTINGS)

    def get(self) -> AngelSettings:
        values = {**DEFAULT_SETTINGS, **self.database.setting_values()}
        style = values["response_style"].title()
        if style not in {"Concise", "Balanced", "Detailed"}:
            style = "Balanced"
        return AngelSettings(
            ollama_url=self._safe_ollama_url(values["ollama_url"]),
            model=values["model"].strip() or DEFAULT_SETTINGS["model"],
            display_name=values["display_name"].strip(),
            city=values["city"].strip(),
            region=values["region"].strip(),
            postal_code=values["postal_code"].strip(),
            response_style=style,
            internet_search_enabled=self._as_bool(values["internet_search_enabled"]),
            memory_enabled=self._as_bool(values["memory_enabled"]),
            read_aloud_enabled=self._as_bool(values["read_aloud_enabled"]),
            voice_name=values["voice_name"].strip(),
            speech_rate=self._as_speech_rate(values["speech_rate"]),
        )

    def update(self, **values: object) -> AngelSettings:
        current = self.get()
        allowed = set(DEFAULT_SETTINGS)
        cleaned: dict[str, str] = {}
        for key, value in values.items():
            if key not in allowed:
                continue
            if isinstance(value, bool):
                cleaned[key] = "true" if value else "false"
            else:
                cleaned[key] = str(value).strip()
        if "ollama_url" in cleaned:
            cleaned["ollama_url"] = self._safe_ollama_url(cleaned["ollama_url"])
        if "response_style" in cleaned and cleaned["response_style"].title() not in {
            "Concise",
            "Balanced",
            "Detailed",
        }:
            cleaned["response_style"] = current.response_style
        if "speech_rate" in cleaned:
            cleaned["speech_rate"] = str(self._as_speech_rate(cleaned["speech_rate"]))
        self.database.set_settings(cleaned)
        return self.get()

    @staticmethod
    def _as_bool(value: str) -> bool:
        return value.strip().lower() in {"1", "true", "yes", "on", "enabled"}

    @staticmethod
    def _safe_ollama_url(value: str) -> str:
        candidate = value.strip().rstrip("/") or DEFAULT_SETTINGS["ollama_url"]
        if not candidate.startswith(("http://", "https://")):
            raise ValueError("Ollama URL must begin with http:// or https://")
        return candidate

    @staticmethod
    def _as_speech_rate(value: str) -> int:
        try:
            rate = int(str(value).strip())
        except ValueError:
            return 0
        return max(-10, min(10, rate))
