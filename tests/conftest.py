from __future__ import annotations

import logging

import pytest

from angel.database import Database
from angel.memory import MemoryService
from angel.settings import SettingsService


@pytest.fixture
def services(tmp_path):
    database = Database(tmp_path / "angel.db", logging.getLogger("test.database"))
    settings = SettingsService(database)
    memory = MemoryService(database, settings)
    return database, settings, memory
