from __future__ import annotations

from dataclasses import dataclass

from .database import Database


DEFAULT_SETTINGS: dict[str, str] = {
    "ollama_url": "http://127.0.0.1:11434",
    "model": "llama3.2:3b",
    "lightweight_model": "llama3.2:3b",
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
    "connectivity_mode": "Auto",
    "resource_profile": "Balanced",
    "technical_level": "Plain language first",
    "formatting_preference": "Natural",
    "workflow_preferences": "",
    "active_project_id": "",
    "auto_start_ollama": "true",
    "coding_model": "",
    "vision_model": "",
    "embedding_model": "Local hashed embeddings",
    "comfyui_url": "http://127.0.0.1:8188",
    "comfyui_model": "",
    "acestep_url": "http://127.0.0.1:8001",
    "acestep_model": "",
    "knowledge_enabled": "true",
}


@dataclass(frozen=True)
class AngelSettings:
    ollama_url: str
    model: str
    lightweight_model: str
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
    connectivity_mode: str
    resource_profile: str
    technical_level: str
    formatting_preference: str
    workflow_preferences: str
    active_project_id: str
    auto_start_ollama: bool
    coding_model: str
    vision_model: str
    embedding_model: str
    comfyui_url: str
    comfyui_model: str
    acestep_url: str
    acestep_model: str
    knowledge_enabled: bool

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
        connectivity_mode = values["connectivity_mode"].title()
        if connectivity_mode not in {"Offline", "Local + Internet Tools", "Auto"}:
            connectivity_mode = "Auto"
        resource_profile = values["resource_profile"].title()
        if resource_profile not in {"Low Resource", "Balanced", "Maximum Quality"}:
            resource_profile = "Balanced"
        return AngelSettings(
            ollama_url=self._safe_ollama_url(values["ollama_url"]),
            model=values["model"].strip() or DEFAULT_SETTINGS["model"],
            lightweight_model=values["lightweight_model"].strip() or DEFAULT_SETTINGS["lightweight_model"],
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
            connectivity_mode=connectivity_mode,
            resource_profile=resource_profile,
            technical_level=values["technical_level"].strip() or "Plain language first",
            formatting_preference=values["formatting_preference"].strip() or "Natural",
            workflow_preferences=values["workflow_preferences"].strip(),
            active_project_id=values["active_project_id"].strip(),
            auto_start_ollama=self._as_bool(values["auto_start_ollama"]),
            coding_model=values["coding_model"].strip(),
            vision_model=values["vision_model"].strip(),
            embedding_model=values["embedding_model"].strip() or "Local hashed embeddings",
            comfyui_url=self._safe_local_service_url(values["comfyui_url"], "http://127.0.0.1:8188"),
            comfyui_model=values["comfyui_model"].strip(),
            acestep_url=self._safe_local_service_url(values["acestep_url"], "http://127.0.0.1:8001"),
            acestep_model=values["acestep_model"].strip(),
            knowledge_enabled=self._as_bool(values["knowledge_enabled"]),
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
        if "connectivity_mode" in cleaned and cleaned["connectivity_mode"].title() not in {
            "Offline", "Local + Internet Tools", "Auto"
        }:
            cleaned["connectivity_mode"] = current.connectivity_mode
        if "resource_profile" in cleaned and cleaned["resource_profile"].title() not in {
            "Low Resource", "Balanced", "Maximum Quality"
        }:
            cleaned["resource_profile"] = current.resource_profile
        for key, fallback in (
            ("comfyui_url", current.comfyui_url),
            ("acestep_url", current.acestep_url),
        ):
            if key in cleaned:
                cleaned[key] = self._safe_local_service_url(cleaned[key], fallback)
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

    @classmethod
    def _safe_local_service_url(cls, value: str, fallback: str) -> str:
        candidate = value.strip().rstrip("/") or fallback
        checked = cls._safe_ollama_url(candidate)
        from urllib.parse import urlparse

        host = (urlparse(checked).hostname or "").lower()
        if host not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("Creator services must use localhost")
        return checked
