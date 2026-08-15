from __future__ import annotations

import socket
import urllib.error

import pytest

from angel.search import SearchResult, SearchService, SearchUnavailableError, is_safe_public_url


class StaticProvider:
    def __init__(self, payload):
        self.payload = payload

    def search(self, query, limit=5):
        return self.payload


class ErrorProvider:
    def __init__(self, error):
        self.error = error

    def search(self, query, limit=5):
        raise self.error


def test_search_result_normalization_and_success():
    service = SearchService(
        StaticProvider(
            [
                {
                    "title": " Example   Result ",
                    "href": "https://example.com/page",
                    "body": " useful   snippet ",
                },
                {"title": "Unsafe", "url": "http://127.0.0.1/admin", "snippet": "no"},
                {"title": "Missing URL", "snippet": "no"},
            ]
        )
    )

    results = service.search("query", limit=5)

    assert results == [
        SearchResult("Example Result", "https://example.com/page", "example.com", "useful snippet")
    ]


def test_search_timeout():
    service = SearchService(ErrorProvider(socket.timeout("late")))
    with pytest.raises(SearchUnavailableError, match="timed out"):
        service.search("query")


def test_search_network_failure():
    service = SearchService(ErrorProvider(urllib.error.URLError("offline")))
    with pytest.raises(SearchUnavailableError, match="unavailable"):
        service.search("query")


@pytest.mark.parametrize("payload", [None, {}, "not a list", [42, None]])
def test_malformed_provider_result(payload):
    service = SearchService(StaticProvider(payload))
    with pytest.raises(SearchUnavailableError):
        service.search("query")


@pytest.mark.parametrize(
    ("url", "safe"),
    [
        ("https://example.com/path", True),
        ("http://localhost/admin", False),
        ("http://10.0.0.2/private", False),
        ("file:///C:/secret", False),
        ("javascript:alert(1)", False),
        ("https://[::1]/", False),
    ],
)
def test_public_url_validation(url, safe):
    assert is_safe_public_url(url) is safe
