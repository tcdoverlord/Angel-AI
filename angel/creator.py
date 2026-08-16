from __future__ import annotations

import json
import mimetypes
import os
import random
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .database import Database, utc_now
from .ollama_client import OllamaClient
from .paths import InstallationLayout, safe_write_json
from .settings import SettingsService


class CreatorUnavailableError(RuntimeError):
    pass


class CreatorGenerationError(RuntimeError):
    pass


@dataclass(frozen=True)
class CapabilityStatus:
    role: str
    installed: bool
    backend: str
    model: str
    message: str


def _local_base_url(value: str) -> str:
    base = value.strip().rstrip("/")
    if not OllamaClient.is_local_url(base):
        raise CreatorUnavailableError("Creator backends must use localhost")
    return base


def _json_request(
    base_url: str,
    path: str,
    *,
    body: dict[str, Any] | None = None,
    timeout: float = 10.0,
) -> dict[str, Any]:
    base = _local_base_url(base_url)
    request = urllib.request.Request(
        base + path,
        data=json.dumps(body).encode("utf-8") if body is not None else None,
        method="POST" if body is not None else "GET",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read(10_000_000).decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        raise CreatorUnavailableError(f"Local creator service is unavailable: {exc}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CreatorGenerationError("Local creator returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise CreatorGenerationError("Local creator returned an unsupported response")
    return payload


class CreatorLibrary:
    def __init__(self, database: Database) -> None:
        self.database = database

    def add(
        self,
        kind: str,
        title: str,
        prompt: str,
        output_path: str,
        backend: str,
        model: str,
        seed: int | None,
        metadata: dict[str, Any],
        status: str = "created",
    ) -> dict[str, Any]:
        now = utc_now()
        with self.database.transaction() as connection:
            cursor = connection.execute(
                "INSERT INTO creator_items(kind, title, prompt, output_path, backend, model, seed, "
                "metadata_json, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    kind[:40], title.strip()[:180], prompt.strip(), output_path, backend[:80],
                    model[:160], seed, json.dumps(metadata, ensure_ascii=False), status[:40], now, now,
                ),
            )
            item_id = int(cursor.lastrowid)
        return self.get(item_id)

    def get(self, item_id: int) -> dict[str, Any]:
        with self.database.connect() as connection:
            row = connection.execute("SELECT * FROM creator_items WHERE id = ?", (item_id,)).fetchone()
        if row is None:
            raise KeyError(f"Creator item {item_id} was not found")
        return self._item(row)

    def list(self, kind: str = "", limit: int = 250) -> list[dict[str, Any]]:
        with self.database.connect() as connection:
            if kind.strip():
                rows = connection.execute(
                    "SELECT * FROM creator_items WHERE kind = ? ORDER BY created_at DESC LIMIT ?",
                    (kind.strip(), max(1, limit)),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM creator_items ORDER BY created_at DESC LIMIT ?",
                    (max(1, limit),),
                ).fetchall()
        return [self._item(row) for row in rows]

    def delete(self, item_id: int, delete_output: bool = False) -> bool:
        item = self.get(item_id)
        with self.database.transaction() as connection:
            cursor = connection.execute("DELETE FROM creator_items WHERE id = ?", (item_id,))
        if delete_output and item["output_path"]:
            try:
                Path(item["output_path"]).unlink(missing_ok=True)
            except OSError:
                pass
        return cursor.rowcount > 0

    @staticmethod
    def _item(row: Any) -> dict[str, Any]:
        item = dict(row)
        try:
            item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
        except (json.JSONDecodeError, TypeError):
            item.pop("metadata_json", None)
            item["metadata"] = {}
        return item


class ComfyUIBackend:
    def __init__(self, settings: SettingsService, layout: InstallationLayout, library: CreatorLibrary) -> None:
        self.settings = settings
        self.layout = layout
        self.library = library

    def status(self) -> CapabilityStatus:
        current = self.settings.get()
        try:
            _json_request(current.comfyui_url, "/system_stats", timeout=3)
            models = self.models()
            model = current.comfyui_model or (models[0] if models else "")
            return CapabilityStatus("Image AI", True, "ComfyUI", model, "Local ComfyUI is ready")
        except (CreatorUnavailableError, CreatorGenerationError):
            return CapabilityStatus(
                "Image AI", False, "ComfyUI", current.comfyui_model,
                "ComfyUI is not installed or not running at the configured localhost URL",
            )

    def models(self) -> list[str]:
        current = self.settings.get()
        payload = _json_request(current.comfyui_url, "/object_info/CheckpointLoaderSimple", timeout=5)
        node = payload.get("CheckpointLoaderSimple", payload)
        try:
            values = node["input"]["required"]["ckpt_name"][0]
        except (KeyError, IndexError, TypeError):
            return []
        return [str(value) for value in values] if isinstance(values, list) else []

    def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        seed: int | None = None,
        steps: int = 20,
        title: str = "",
    ) -> dict[str, Any]:
        current = self.settings.get()
        models = self.models()
        model = current.comfyui_model or (models[0] if models else "")
        if not model:
            raise CreatorUnavailableError("ComfyUI is running, but no checkpoint model was found")
        chosen_seed = int(seed if seed is not None else random.SystemRandom().randrange(0, 2**63 - 1))
        width = max(256, min(2048, int(width))) // 8 * 8
        height = max(256, min(2048, int(height))) // 8 * 8
        steps = max(1, min(100, int(steps)))
        workflow: dict[str, Any] = {
            "3": {"class_type": "KSampler", "inputs": {"seed": chosen_seed, "steps": steps, "cfg": 7.0, "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0, "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]}},
            "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": model}},
            "5": {"class_type": "EmptyLatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
            "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt.strip(), "clip": ["4", 1]}},
            "7": {"class_type": "CLIPTextEncode", "inputs": {"text": negative_prompt.strip(), "clip": ["4", 1]}},
            "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
            "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "Angel", "images": ["8", 0]}},
        }
        queued = _json_request(
            current.comfyui_url, "/prompt",
            body={"prompt": workflow, "client_id": f"angel-{uuid.uuid4().hex}"}, timeout=15,
        )
        prompt_id = str(queued.get("prompt_id") or "")
        if not prompt_id:
            raise CreatorGenerationError("ComfyUI did not return a prompt ID")
        deadline = time.monotonic() + 600
        image: dict[str, Any] | None = None
        while time.monotonic() < deadline:
            history = _json_request(current.comfyui_url, f"/history/{prompt_id}", timeout=10)
            record = history.get(prompt_id)
            if isinstance(record, dict):
                output = record.get("outputs", {}).get("9", {})
                images = output.get("images", []) if isinstance(output, dict) else []
                if images and isinstance(images[0], dict):
                    image = images[0]
                    break
                status = record.get("status", {})
                if isinstance(status, dict) and status.get("status_str") == "error":
                    raise CreatorGenerationError("ComfyUI reported a generation error")
            time.sleep(1)
        if image is None:
            raise CreatorGenerationError("ComfyUI image generation timed out")
        query = urllib.parse.urlencode(
            {"filename": image.get("filename", ""), "subfolder": image.get("subfolder", ""), "type": image.get("type", "output")}
        )
        request = urllib.request.Request(_local_base_url(current.comfyui_url) + "/view?" + query)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                image_bytes = response.read(100_000_000)
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            raise CreatorGenerationError(f"ComfyUI output could not be downloaded: {exc}") from exc
        filename = f"angel-image-{datetime_stamp()}-{chosen_seed}.png"
        output_path = self.layout.generated_images / filename
        output_path.write_bytes(image_bytes)
        metadata = {
            "prompt": prompt, "negative_prompt": negative_prompt, "width": width, "height": height,
            "steps": steps, "seed": chosen_seed, "backend_prompt_id": prompt_id, "generation_date": utc_now(),
        }
        safe_write_json(output_path.with_suffix(".json"), metadata)
        return self.library.add(
            "image", title or prompt[:80], prompt, str(output_path), "ComfyUI", model,
            chosen_seed, metadata,
        )


class AceStepBackend:
    def __init__(self, settings: SettingsService, layout: InstallationLayout, library: CreatorLibrary) -> None:
        self.settings = settings
        self.layout = layout
        self.library = library

    def status(self) -> CapabilityStatus:
        current = self.settings.get()
        try:
            _json_request(current.acestep_url, "/health", timeout=3)
            models = self.models()
            model = current.acestep_model or (models[0] if models else "")
            return CapabilityStatus("Music AI", True, "ACE-Step 1.5", model, "Local ACE-Step is ready")
        except (CreatorUnavailableError, CreatorGenerationError):
            return CapabilityStatus(
                "Music AI", False, "ACE-Step 1.5", current.acestep_model,
                "ACE-Step 1.5 is not installed or not running at the configured localhost URL",
            )

    def models(self) -> list[str]:
        current = self.settings.get()
        payload = _json_request(current.acestep_url, "/v1/models", timeout=5)
        data = payload.get("data", [])
        if isinstance(data, dict):
            data = data.get("data", data.get("models", []))
        if not isinstance(data, list):
            return []
        return [str(item.get("id") or item.get("name") or item) for item in data]

    def generate(
        self,
        title: str,
        description: str,
        genre: str,
        mood: str,
        lyrics: str,
        instrumental: bool,
        vocal_style: str,
        duration: int,
        seed: int | None = None,
    ) -> dict[str, Any]:
        current = self.settings.get()
        prompt = ", ".join(part for part in (description, genre, mood, vocal_style) if part.strip())
        chosen_seed = int(seed if seed is not None else random.SystemRandom().randrange(1, 2**31 - 1))
        model = current.acestep_model
        request_body: dict[str, Any] = {
            "prompt": prompt,
            "lyrics": "" if instrumental else lyrics,
            "audio_duration": max(10, min(600, int(duration))),
            "audio_format": "wav",
            "seed": chosen_seed,
            "thinking": True,
        }
        if model:
            request_body["model"] = model
        released = _json_request(current.acestep_url, "/release_task", body=request_body, timeout=30)
        data = released.get("data", released)
        task_id = str(data.get("task_id") or "") if isinstance(data, dict) else ""
        if not task_id:
            raise CreatorGenerationError("ACE-Step did not return a task ID")
        deadline = time.monotonic() + 1800
        result_item: dict[str, Any] | None = None
        while time.monotonic() < deadline:
            queried = _json_request(
                current.acestep_url, "/query_result", body={"task_id_list": [task_id]}, timeout=15
            )
            records = queried.get("data", [])
            if isinstance(records, dict):
                records = [records]
            record = records[0] if isinstance(records, list) and records else None
            if isinstance(record, dict):
                status = int(record.get("status") or 0)
                if status == 2:
                    raise CreatorGenerationError("ACE-Step reported that music generation failed")
                if status == 1:
                    result = record.get("result", "[]")
                    try:
                        parsed = json.loads(result) if isinstance(result, str) else result
                    except json.JSONDecodeError as exc:
                        raise CreatorGenerationError("ACE-Step returned malformed result metadata") from exc
                    if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
                        result_item = parsed[0]
                        break
            time.sleep(2)
        if result_item is None:
            raise CreatorGenerationError("ACE-Step music generation timed out")
        file_url = str(result_item.get("file") or "")
        if not file_url:
            raise CreatorGenerationError("ACE-Step returned no audio file")
        download_url = urllib.parse.urljoin(_local_base_url(current.acestep_url) + "/", file_url)
        if not OllamaClient.is_local_url(download_url):
            raise CreatorGenerationError("ACE-Step returned a non-local output URL")
        try:
            with urllib.request.urlopen(download_url, timeout=120) as response:
                audio_bytes = response.read(1_000_000_000)
                content_type = response.headers.get_content_type()
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            raise CreatorGenerationError(f"ACE-Step audio could not be downloaded: {exc}") from exc
        extension = mimetypes.guess_extension(content_type) or Path(urllib.parse.urlparse(file_url).path).suffix or ".mp3"
        output_path = self.layout.generated_music / f"angel-song-{datetime_stamp()}-{chosen_seed}{extension}"
        output_path.write_bytes(audio_bytes)
        metadata = {
            "title": title, "description": description, "genre": genre, "mood": mood,
            "lyrics": "" if instrumental else lyrics, "instrumental": instrumental,
            "vocal_style": vocal_style, "duration": duration, "seed": chosen_seed,
            "task_id": task_id, "generation_date": utc_now(), "backend_result": result_item,
        }
        safe_write_json(output_path.with_suffix(output_path.suffix + ".json"), metadata)
        return self.library.add(
            "song", title or description[:80], prompt, str(output_path), "ACE-Step 1.5",
            model or str(result_item.get("dit_model") or ""), chosen_seed, metadata,
        )


class ModelRouter:
    def __init__(self, settings: SettingsService, images: ComfyUIBackend, music: AceStepBackend) -> None:
        self.settings = settings
        self.images = images
        self.music = music

    def statuses(self, chat_ready: bool, installed_chat_models: list[str]) -> list[CapabilityStatus]:
        current = self.settings.get()
        image = self.images.status()
        music = self.music.status()
        return [
            CapabilityStatus("Primary Chat", chat_ready, "Ollama", current.model, "Ready" if chat_ready else "Ollama/model unavailable"),
            CapabilityStatus(
                "Lightweight Chat",
                bool(current.lightweight_model and current.lightweight_model in installed_chat_models),
                "Ollama", current.lightweight_model,
                "Small fallback role; defaults to llama3.2:3b and never downloads automatically",
            ),
            CapabilityStatus("Coding", bool(current.coding_model and current.coding_model in installed_chat_models), "Ollama", current.coding_model, "Uses Primary Chat when no specialist is selected"),
            CapabilityStatus("Vision", bool(current.vision_model and current.vision_model in installed_chat_models), "Ollama", current.vision_model, "Optional local vision model"),
            CapabilityStatus(
                "Embeddings", True,
                "Ollama" if not current.embedding_model.lower().startswith("local hash") else "Angel deterministic local fallback",
                current.embedding_model,
                "Real local Ollama embeddings when configured; deterministic local retrieval vectors otherwise",
            ),
            CapabilityStatus("Image", image.installed, image.backend, image.model, image.message),
            CapabilityStatus("Music", music.installed, music.backend, music.model, music.message),
        ]


def datetime_stamp() -> str:
    return time.strftime("%Y%m%d-%H%M%S")
