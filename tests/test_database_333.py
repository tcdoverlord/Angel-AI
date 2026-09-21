from pathlib import Path

from angel_platform.storage.database import AngelDatabase


def test_database_records_messages_and_stats(tmp_path: Path):
    db = AngelDatabase(tmp_path / "angel.sqlite3")
    db.record_message("user", "hello", "conversation-1")
    db.record_message("assistant", "hello back", "conversation-1")
    messages = db.list_messages("conversation-1")
    assert [item["role"] for item in messages] == ["user", "assistant"]
    assert db.stats()["messages"] == 2


def test_database_memory_requires_approval_for_retrieval(tmp_path: Path):
    db = AngelDatabase(tmp_path / "angel.sqlite3")
    db.add_memory("approved fact", approved=True)
    db.add_memory("unapproved fact", approved=False)
    results = db.search_memories("fact")
    assert [item["content"] for item in results] == ["approved fact"]


def test_database_feedback_and_audit(tmp_path: Path):
    db = AngelDatabase(tmp_path / "angel.sqlite3")
    assert db.record_feedback("incomplete", "Add rollback steps") > 0
    assert db.audit_tool("system_health", "preview", {"read_only": True}) > 0
    stats = db.stats()
    assert stats["feedback"] == 1
    assert stats["tool_audit"] == 1
