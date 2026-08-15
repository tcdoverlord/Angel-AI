from __future__ import annotations

import ipaddress
import logging
import socket
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from typing import Any, Protocol


class SearchUnavailableError(RuntimeError):
    pass


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    domain: str
    snippet: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


class SearchProvider(Protocol):
    def search(self, query: str, limit: int = 5) -> list[Any]: ...


def is_safe_public_url(url: str) -> bool:
    try:
        parsed = urllib.parse.urlparse(url)
    except ValueError:
        return False
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    hostname = parsed.hostname.lower().rstrip(".")
    if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(".local"):
        return False
    try:
        address = ipaddress.ip_address(hostname.strip("[]"))
    except ValueError:
        return True
    return not (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    )


class BingRssSearchProvider:
    """No-key public web search using Bing's documented RSS result format."""

    endpoint = "https://www.bing.com/search"

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    def search(self, query: str, limit: int = 5) -> list[dict[str, str]]:
        clean_query = " ".join(query.split()).strip()
        if not clean_query:
            raise ValueError("Search query cannot be empty")
        params = urllib.parse.urlencode({"q": clean_query, "format": "rss", "count": limit})
        request = urllib.request.Request(
            f"{self.endpoint}?{params}",
            headers={
                "User-Agent": "Angel Local Personal AI/Windows",
                "Accept": "application/rss+xml, application/xml;q=0.9",
            },
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            payload = response.read(1_500_000)
        root = ET.fromstring(payload)
        results: list[dict[str, str]] = []
        for item in root.findall("./channel/item"):
            results.append(
                {
                    "title": (item.findtext("title") or "").strip(),
                    "url": (item.findtext("link") or "").strip(),
                    "snippet": (item.findtext("description") or "").strip(),
                }
            )
            if len(results) >= limit:
                break
        return results


class SearchService:
    def __init__(
        self,
        provider: SearchProvider | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.provider = provider or BingRssSearchProvider()
        self.logger = logger or logging.getLogger("angel.search")

    def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        clean_query = " ".join(query.split()).strip()
        if not clean_query:
            raise ValueError("Search query cannot be empty")
        try:
            raw_results = self.provider.search(clean_query, max(1, min(limit, 8)))
            results = self.normalize(raw_results, max(1, min(limit, 8)))
        except (TimeoutError, socket.timeout) as exc:
            self.logger.warning("Web search timed out: %s", exc)
            raise SearchUnavailableError("Web search timed out") from exc
        except (urllib.error.URLError, ET.ParseError, OSError) as exc:
            self.logger.warning("Web search failed: %s", exc)
            raise SearchUnavailableError("Web search is currently unavailable") from exc
        except SearchUnavailableError:
            raise
        except Exception as exc:
            self.logger.exception("Unexpected web search failure")
            raise SearchUnavailableError("Web search is currently unavailable") from exc
        if not results:
            raise SearchUnavailableError("Web search returned no usable public results")
        return results

    @staticmethod
    def normalize(raw_results: Any, limit: int = 5) -> list[SearchResult]:
        if not isinstance(raw_results, (list, tuple)):
            raise SearchUnavailableError("Search provider returned malformed results")
        normalized: list[SearchResult] = []
        seen: set[str] = set()
        for raw in raw_results:
            if isinstance(raw, SearchResult):
                title, url, snippet = raw.title, raw.url, raw.snippet
            elif isinstance(raw, dict):
                title = str(raw.get("title") or raw.get("name") or "").strip()
                url = str(raw.get("url") or raw.get("href") or raw.get("link") or "").strip()
                snippet = str(
                    raw.get("snippet") or raw.get("body") or raw.get("description") or ""
                ).strip()
            else:
                continue
            if not title or not is_safe_public_url(url) or url in seen:
                continue
            parsed = urllib.parse.urlparse(url)
            domain = (parsed.hostname or "").lower()
            normalized.append(
                SearchResult(
                    title=" ".join(title.split())[:240],
                    url=url,
                    domain=domain,
                    snippet=" ".join(snippet.split())[:700],
                )
            )
            seen.add(url)
            if len(normalized) >= limit:
                break
        return normalized
