from __future__ import annotations

import json
import logging
import socket
import urllib.error
import urllib.parse
import urllib.request
import ipaddress
from typing import Any


class OllamaError(RuntimeError):
    pass


class OllamaClient:
    def __init__(self, logger: logging.Logger | None = None, timeout: float = 90.0) -> None:
        self.logger = logger or logging.getLogger("angel.ollama")
        self.timeout = timeout

    @staticmethod
    def _endpoint(base_url: str, path: str) -> str:
        parsed = urllib.parse.urlparse(base_url.rstrip("/"))
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise OllamaError("Ollama URL is invalid")
        return base_url.rstrip("/") + path

    @staticmethod
    def is_local_url(base_url: str) -> bool:
        try:
            host = (urllib.parse.urlparse(base_url).hostname or "").lower()
            if host in {"localhost", "localhost.localdomain"}:
                return True
            return ipaddress.ip_address(host).is_loopback
        except (ValueError, TypeError):
            return False

    def list_model_details(self, base_url: str) -> list[dict[str, Any]]:
        payload = self._request(base_url, "/api/tags", method="GET", timeout=5.0)
        models = payload.get("models", []) if isinstance(payload, dict) else []
        return [dict(model) for model in models if isinstance(model, dict)]

    def list_models(self, base_url: str) -> list[str]:
        models = self.list_model_details(base_url)
        names: list[str] = []
        for model in models:
            if isinstance(model, dict):
                name = model.get("name") or model.get("model")
                if isinstance(name, str) and name.strip():
                    names.append(name.strip())
        return names

    def check(self, base_url: str) -> tuple[bool, list[str]]:
        try:
            return True, self.list_models(base_url)
        except OllamaError:
            return False, []

    def chat(self, base_url: str, model: str, messages: list[dict[str, str]]) -> str:
        payload = self._request(
            base_url,
            "/api/chat",
            method="POST",
            body={"model": model, "messages": messages, "stream": False},
            timeout=self.timeout,
        )
        content: Any = None
        if isinstance(payload, dict):
            message = payload.get("message")
            if isinstance(message, dict):
                content = message.get("content")
            if not content:
                content = payload.get("response")
        if not isinstance(content, str) or not content.strip():
            raise OllamaError("Ollama returned an empty or unsupported response")
        return content.strip()

    def embed(self, base_url: str, model: str, inputs: str | list[str]) -> list[list[float]]:
        """Create real embeddings with an explicitly configured local Ollama model."""
        values = [inputs] if isinstance(inputs, str) else list(inputs)
        if not model.strip() or not values:
            raise OllamaError("A local embedding model and input are required")
        payload = self._request(
            base_url,
            "/api/embed",
            method="POST",
            body={"model": model.strip(), "input": values},
            timeout=self.timeout,
        )
        embeddings = payload.get("embeddings") if isinstance(payload, dict) else None
        if not isinstance(embeddings, list) or len(embeddings) != len(values):
            raise OllamaError("Ollama returned invalid embedding vectors")
        checked: list[list[float]] = []
        for vector in embeddings:
            if not isinstance(vector, list) or not vector:
                raise OllamaError("Ollama returned an empty embedding vector")
            try:
                checked.append([float(value) for value in vector])
            except (TypeError, ValueError) as exc:
                raise OllamaError("Ollama returned a malformed embedding vector") from exc
        return checked

    def _request(
        self,
        base_url: str,
        path: str,
        method: str,
        body: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        url = self._endpoint(base_url, path)
        data = json.dumps(body).encode("utf-8") if body is not None else None
        request = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout or self.timeout) as response:
                raw = response.read(5_000_000)
            payload = json.loads(raw.decode("utf-8"))
            if not isinstance(payload, dict):
                raise OllamaError("Ollama returned malformed JSON")
            return payload
        except (urllib.error.URLError, urllib.error.HTTPError, socket.timeout, TimeoutError) as exc:
            self.logger.warning("Ollama request failed: %s", exc)
            raise OllamaError("Local AI is unavailable. Check Ollama in Settings.") from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            self.logger.warning("Ollama returned invalid data: %s", exc)
            raise OllamaError("Local AI returned an invalid response") from exc
