from __future__ import annotations

import sqlite3

from angel.database import Database


def test_foundation_database_migrates_without_data_loss(tmp_path):
    path = tmp_path / "foundation.db"
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL
        );
        CREATE TABLE messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL
        );
        CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        INSERT INTO conversations(id, title) VALUES (1, 'Existing conversation');
        INSERT INTO messages(conversation_id, role, content) VALUES (1, 'user', 'Keep me');
        INSERT INTO settings(key, value) VALUES ('model', 'existing-model');
        """
    )
    connection.commit()
    connection.close()

    database = Database(path)
    database.initialize()

    assert database.list_conversations()[0]["title"] == "Existing conversation"
    assert database.get_messages(1)[0]["content"] == "Keep me"
    assert database.setting_values()["model"] == "existing-model"
    with database.connect() as migrated:
        tables = {
            row[0]
            for row in migrated.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        message_columns = {
            row[1] for row in migrated.execute("PRAGMA table_info(messages)")
        }
    assert {"memories", "recommendation_history", "tool_activity"} <= tables
    assert {"sources_json", "created_at"} <= message_columns
