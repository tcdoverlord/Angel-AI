from __future__ import annotations

import mimetypes
import json
import struct
import wave
import zipfile
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
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
    ".htm",
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
            "metadata": {},
        }
        status, excerpt, metadata = extract_file_text(path, MAX_EXCERPT_CHARS)
        attachment["metadata"] = metadata
        if excerpt:
            attachment["parse_status"] = status
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
        metadata = attachment.get("metadata")
        if isinstance(metadata, dict) and metadata:
            safe_metadata = ", ".join(
                f"{key}: {value}" for key, value in list(metadata.items())[:12]
            )
            sections.append(f"Local metadata for {name}: {safe_metadata}")
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


def _read_text_excerpt(
    path: Path,
    maximum_chars: int = MAX_EXCERPT_CHARS,
    maximum_bytes: int = MAX_READ_BYTES,
) -> str:
    try:
        with path.open("rb") as handle:
            data = handle.read(maximum_bytes)
    except OSError:
        return ""
    if not data or b"\x00" in data[:4_096]:
        return ""
    text = data.decode("utf-8", errors="replace")
    replacement_ratio = text.count("\ufffd") / max(1, len(text))
    if replacement_ratio > 0.05:
        return ""
    clean = text.strip()
    if len(clean) > maximum_chars:
        clean = clean[:maximum_chars] + "\n[Text excerpt truncated by Angel]"
    return clean


class _PlainHTML(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        clean = " ".join(data.split())
        if clean:
            self.parts.append(clean)


def extract_file_text(
    path: str | Path, maximum_chars: int = MAX_EXCERPT_CHARS
) -> tuple[str, str, dict[str, Any]]:
    """Locally parse supported files without claiming unsupported content was read."""
    target = Path(path)
    suffix = target.suffix.lower()
    text = ""
    metadata: dict[str, Any] = {}
    try:
        if suffix in TEXT_EXTENSIONS:
            text = _read_text_excerpt(
                target,
                maximum_chars=maximum_chars,
                maximum_bytes=max(MAX_READ_BYTES, min(8_000_000, maximum_chars * 4)),
            )
            if suffix in {".html", ".htm"} and text:
                parser = _PlainHTML()
                parser.feed(text)
                text = "\n".join(parser.parts)
            elif suffix == ".json" and text:
                try:
                    text = json.dumps(json.loads(text), ensure_ascii=False, indent=2)
                except json.JSONDecodeError:
                    pass
        elif suffix == ".docx":
            text = _docx_text(target)
        elif suffix == ".xlsx":
            text = _xlsx_text(target)
        elif suffix == ".pdf":
            text = _pdf_text(target)
        elif suffix == ".wav":
            with wave.open(str(target), "rb") as audio:
                frames = audio.getnframes()
                rate = audio.getframerate()
                metadata = {
                    "duration_seconds": round(frames / rate, 2) if rate else 0,
                    "channels": audio.getnchannels(),
                    "sample_rate": rate,
                    "sample_width_bytes": audio.getsampwidth(),
                }
        elif suffix in {".png", ".gif", ".jpg", ".jpeg"}:
            metadata = _image_metadata(target)
    except (OSError, ValueError, ET.ParseError, zipfile.BadZipFile):
        return "metadata_only", "", metadata
    clean = text.strip()
    if not clean:
        return "metadata_only", "", metadata
    if len(clean) > maximum_chars:
        clean = clean[:maximum_chars].rstrip() + "\n[Text excerpt truncated by Angel]"
    return "text_extracted", clean, metadata


def _docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    paragraphs: list[str] = []
    for paragraph in root.iter(namespace + "p"):
        line = "".join(node.text or "" for node in paragraph.iter(namespace + "t"))
        if line.strip():
            paragraphs.append(line.strip())
    return "\n".join(paragraphs)


def _xlsx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = ["".join(node.text or "" for node in item.iter() if node.tag.endswith("}t")) for item in root]
        lines: list[str] = []
        sheets = sorted(name for name in archive.namelist() if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"))
        for sheet_name in sheets[:20]:
            root = ET.fromstring(archive.read(sheet_name))
            lines.append(f"[{Path(sheet_name).stem}]")
            for row in (node for node in root.iter() if node.tag.endswith("}row")):
                values: list[str] = []
                for cell in (node for node in row if node.tag.endswith("}c")):
                    cell_type = cell.attrib.get("t", "")
                    value_node = next((node for node in cell.iter() if node.tag.endswith("}v")), None)
                    value = value_node.text if value_node is not None and value_node.text else ""
                    if cell_type == "s" and value.isdigit() and int(value) < len(shared):
                        value = shared[int(value)]
                    elif cell_type == "inlineStr":
                        value = "".join(node.text or "" for node in cell.iter() if node.tag.endswith("}t"))
                    values.append(value)
                if any(values):
                    lines.append("\t".join(values))
    return "\n".join(lines)


def _pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore[import-not-found]
    except ImportError:
        return ""
    reader = PdfReader(str(path))
    return "\n\n".join((page.extract_text() or "").strip() for page in reader.pages[:200])


def _image_metadata(path: Path) -> dict[str, Any]:
    data = path.read_bytes()[:512_000]
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        width, height = struct.unpack(">II", data[16:24])
        return {"width": width, "height": height}
    if data[:6] in {b"GIF87a", b"GIF89a"} and len(data) >= 10:
        width, height = struct.unpack("<HH", data[6:10])
        return {"width": width, "height": height}
    if data.startswith(b"\xff\xd8"):
        index = 2
        while index + 9 < len(data):
            if data[index] != 0xFF:
                index += 1
                continue
            marker = data[index + 1]
            length = int.from_bytes(data[index + 2 : index + 4], "big")
            if marker in range(0xC0, 0xC4) and length >= 7:
                height = int.from_bytes(data[index + 5 : index + 7], "big")
                width = int.from_bytes(data[index + 7 : index + 9], "big")
                return {"width": width, "height": height}
            index += max(2, length + 2)
    return {}
