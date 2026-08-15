from __future__ import annotations

import pytest

from angel.memory import MemoryDisabledError


def test_memory_save_search_and_delete(services):
    _database, _settings, memory = services
    saved = memory.add("I prefer deep purple interfaces.", "preference")

    results = memory.search("purple interface")

    assert results[0]["id"] == saved["id"]
    assert results[0]["category"] == "preference"
    assert memory.delete(saved["id"]) is True
    assert memory.search("purple interface") == []


def test_memory_deduplicates_case_insensitively(services):
    _database, _settings, memory = services
    first = memory.add("I am working on StimTake.", "project")
    second = memory.add("i am working on stimtake.", "general")

    assert first["id"] == second["id"]
    assert memory.get(first["id"])["category"] == "general"


def test_memory_disabled_behavior(services):
    _database, settings, memory = services
    settings.update(memory_enabled=False)

    with pytest.raises(MemoryDisabledError):
        memory.add("This must not be saved")
    with pytest.raises(MemoryDisabledError):
        memory.search("saved")
    with pytest.raises(MemoryDisabledError):
        memory.delete(1)


def test_memory_rejects_unknown_category(services):
    _database, _settings, memory = services
    with pytest.raises(ValueError):
        memory.add("A valid thought", "secret")
