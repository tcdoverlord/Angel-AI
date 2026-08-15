from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any, Iterable


MAX_ATTACHMENTS = 20
MAX_READ_BYTES = 256_000
MAX_EXCERPT_CHARS = 12_000
TEXT_EXTENSIONS = {
    ".bat",
    ".cfg",
    ".conf",
    ".css",
    ".csv",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".log",
    ".md",
    ".ps1",
    ".py",
    ".rtf",
    ".sql",
    ".toml",
    ".ts",
    ".tsv",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}


def media_kind(mime_type: str, suffix: str) -> str:
    primary = mime_type.split("/", 1)[0].lower()
    if primary in {"image", "audio", "video", "text"}:
        return primary
    if suffix.lower() in TEXT_EXTENSIONS:
        return "text"
    if mime_type == "application/pdf":
        return "document"
    if suffix.lower() in {".doc", ".docx", ".odt", ".pages"}:
        return "document"
    if suffix.lower() in {".xls", ".xlsx", ".ods"}:
        return "spreadsheet"
    if suffix.lower() in {".ppt", ".pptx", ".odp"}:
        return "presentation"
    if suffix.lower() in {".zip", ".7z", ".rar", ".tar", ".gz"}:
        return "archive"
    return "file"


def prepare_attachments(paths: Iterable[str | Path]) -> list[dict[str, Any]]:
    """Prepare explicitly selected files without executing or modifying them."""
    attachments: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw_path in paths:
        if len(attachments) >= MAX_ATTACHMENTS:
            break
        try:
            path = Path(raw_path).expanduser().resolve()
            normalized = str(path).casefold()
            if normalized in seen or not path.is_file():
                continue
            size = path.stat().st_size
        except OSError:
            continue
        seen.add(normalized)
        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        kind = media_kind(mime_type, path.suffix)
        attachment: dict[str, Any] = {
            "name": path.name,
            "path": str(path),
            "mime_type": mime_type,
            "media_kind": kind,
            "size": size,
            "parse_status": "metadata_only",
            "text_excerpt": "",
        }
        if kind == "text":
            excerpt = _read_text_excerpt(path)
            if excerpt:
                attachment["parse_status"] = "text_extracted"
                attachment["text_excerpt"] = excerpt
        attachments.append(attachment)
    return attachments


def attachment_context(attachments: list[dict[str, Any]]) -> str:
    if not attachments:
        return ""
    sections = [
        "ATTACHMENTS EXPLICITLY SELECTED BY THE USER",
        "Do not claim to see or hear metadata-only files. Use extracted text only when supplied.",
    ]
    for attachment in attachments:
        name = str(attachment.get("name") or "unnamed file")
        kind = str(attachment.get("media_kind") or "file")
        mime_type = str(attachment.get("mime_type") or "application/octet-stream")
        size = int(attachment.get("size") or 0)
        status = str(attachment.get("parse_status") or "metadata_only")
        sections.append(
            f"File: {name}\nType: {kind} ({mime_type})\nSize: {format_size(size)}\n"
            f"Availability: {'text excerpt available' if status == 'text_extracted' else 'metadata only; content not parsed'}"
        )
        excerpt = str(attachment.get("text_excerpt") or "")
        if status == "text_extracted" and excerpt:
            sections.append(f"Extracted text from {name}:\n{excerpt[:MAX_EXCERPT_CHARS]}")
    return "\n\n".join(sections)


def format_size(size: int) -> str:
    value = float(max(0, size))
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def _read_text_excerpt(path: Path) -> str:
    try:
        data = path.read_bytes()[:MAX_READ_BYTES]
    except OSError:
        return ""
    if not data or b"\x00" in data[:4_096]:
        return ""
    text = data.decode("utf-8", errors="replace")
    replacement_ratio = text.count("\ufffd") / max(1, len(text))
    if replacement_ratio > 0.05:
        return ""
    clean = text.strip()
    if len(clean) > MAX_EXCERPT_CHARS:
        clean = clean[:MAX_EXCERPT_CHARS] + "\n[Text excerpt truncated by Angel]"
    return clean
