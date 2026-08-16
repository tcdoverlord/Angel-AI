from __future__ import annotations

import logging
from pathlib import Path

from angel.backups import BackupService, recover_database_if_needed
from angel.database import Database
from angel.knowledge import KnowledgeService
from angel.memory import MemoryService
from angel.paths import installation_layout, migrate_legacy_data
from angel.projects import ProjectService
from angel.settings import SettingsService


def make_persistent_services(tmp_path):
    layout = installation_layout(tmp_path / "AngelData")
    database = Database(layout.database, logging.getLogger("test.persistence"))
    settings = SettingsService(database)
    memory = MemoryService(database, settings)
    projects = ProjectService(database, settings)
    knowledge = KnowledgeService(database, settings, layout)
    backups = BackupService(database, layout, keep=5)
    return layout, database, settings, memory, projects, knowledge, backups


def test_projects_keep_state_records_and_active_context(tmp_path):
    _layout, _database, _settings, _memory, projects, _knowledge, _backups = make_persistent_services(tmp_path)
    project = projects.create("Angel AI", "Build one persistent local assistant")
    projects.update(int(project["id"]), current_state="Adding project memory and backups")
    projects.add_item(int(project["id"]), "decision", "Use SQLite", "Keep durable state outside cache")
    projects.add_item(int(project["id"]), "todo", "Offline acceptance", "Disconnect external tools")
    projects.set_active(int(project["id"]))

    reopened = ProjectService(Database(_database.path), SettingsService(Database(_database.path)))
    active = reopened.active()

    assert active is not None
    assert active["name"] == "Angel AI"
    assert "project memory and backups" in active["current_state"]
    assert "Use SQLite" in reopened.context("Continue Angel")
    assert len(reopened.items(int(active["id"]))) == 2


def test_cache_deletion_preserves_conversations_memory_projects_settings_and_restore(tmp_path):
    layout, database, settings, memory, projects, _knowledge, backups = make_persistent_services(tmp_path)
    conversation_id = database.create_conversation("Persistent conversation")
    database.add_message(conversation_id, "user", "Keep this after cache cleanup")
    saved_memory = memory.add("My Angel project uses persistent SQLite storage.", "project")
    project = projects.create("Angel AI", "Persistent assistant")
    projects.update(int(project["id"]), current_state="Backup acceptance ready")
    settings.update(display_name="Tony", connectivity_mode="Offline")
    cache_file = layout.cache / "disposable.tmp"
    cache_file.write_text("delete me", encoding="utf-8")
    backup = backups.create("cache survival test")

    settings.update(display_name="Mutated")
    backups.clear_cache()

    assert layout.cache.is_dir()
    assert not cache_file.exists()
    assert database.get_messages(conversation_id)[0]["content"] == "Keep this after cache cleanup"
    assert memory.get(int(saved_memory["id"]))["text"].startswith("My Angel project")
    assert projects.get(int(project["id"]))["current_state"] == "Backup acceptance ready"

    backups.restore(backup.path)
    reopened = Database(layout.database)
    assert SettingsService(reopened).get().display_name == "Tony"
    assert SettingsService(reopened).get().connectivity_mode == "Offline"
    assert reopened.conversation_exists(conversation_id)
    assert ProjectService(reopened, SettingsService(reopened)).get(int(project["id"]))["current_state"] == "Backup acceptance ready"
    assert reopened.integrity_check()[0] is True


def test_corrupt_database_is_preserved_and_newest_valid_backup_is_restored(tmp_path):
    layout, database, _settings, _memory, _projects, _knowledge, backups = make_persistent_services(tmp_path)
    conversation_id = database.create_conversation("Recover me")
    database.add_message(conversation_id, "user", "Durable data")
    backups.create("recovery test")
    database.checkpoint()
    layout.database.write_bytes(b"not a sqlite database")

    result = recover_database_if_needed(layout)
    recovered = Database(layout.database)

    assert result.startswith("restored:")
    assert recovered.conversation_exists(conversation_id)
    assert list(layout.data.glob("angel.corrupt-*.db"))


def test_knowledge_is_local_chunked_deduplicated_and_searchable(tmp_path):
    layout, _database, _settings, _memory, _projects, knowledge, _backups = make_persistent_services(tmp_path)
    source = tmp_path / "camera-notes.txt"
    source.write_text(
        "OBSBOT Tiny 2 camera project. Use 4K30 for detail and 1080p60 for smoother motion. " * 120,
        encoding="utf-8",
    )

    first = knowledge.add(source)
    second = knowledge.add(source)
    results = knowledge.search("Which camera mode gives smoother motion?", limit=3)

    assert first["id"] == second["id"]
    assert first["chunk_count"] > 1
    assert results
    assert "1080p60" in results[0]["content"]
    assert Path(first["stored_path"]).parent == layout.knowledge
    assert knowledge.reindex(int(first["id"]))["chunk_count"] == first["chunk_count"]
    assert knowledge.remove(int(first["id"])) is True
    assert not Path(first["stored_path"]).exists()


def test_legacy_localappdata_database_is_copied_once_without_overwrite(tmp_path, monkeypatch):
    legacy_root = tmp_path / "LocalAppData" / "Angel"
    legacy_root.mkdir(parents=True)
    legacy_database = Database(legacy_root / "angel.db")
    conversation_id = legacy_database.create_conversation("Legacy conversation")
    layout = installation_layout(tmp_path / "NewAngelData")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "LocalAppData"))

    assert migrate_legacy_data(layout) is True
    migrated = Database(layout.database)
    assert migrated.conversation_exists(conversation_id)

    migrated.create_conversation("Newer data")
    assert migrate_legacy_data(layout) is False
    assert len(migrated.list_conversations()) == 2
