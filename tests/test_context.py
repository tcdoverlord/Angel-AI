from __future__ import annotations

from angel.context import ContextBuilder


def test_context_includes_relevant_memory_and_settings(services):
    database, settings, memory = services
    settings.update(display_name="Tony", city="Indianapolis", region="IN", response_style="Concise")
    memory.add("I prefer purple interfaces.", "preference")
    conversation_id = database.create_conversation()
    database.add_message(conversation_id, "user", "Earlier message")

    messages = ContextBuilder(database, settings, memory).build(
        conversation_id, "What interface color do I prefer?"
    )

    system = messages[0]["content"]
    assert "Display name: Tony" in system
    assert "Indianapolis, IN" in system
    assert "I prefer purple interfaces." in system
    assert messages[-1] == {"role": "user", "content": "What interface color do I prefer?"}


def test_context_history_is_limited(services):
    database, settings, memory = services
    conversation_id = database.create_conversation()
    for index in range(20):
        database.add_message(conversation_id, "user", f"message {index}")
        database.add_message(conversation_id, "assistant", f"answer {index}")

    messages = ContextBuilder(database, settings, memory, history_limit=6).build(
        conversation_id, "new message"
    )

    assert len(messages) <= 8
    assert not any(item["content"] == "message 0" for item in messages)
    assert messages[-1]["content"] == "new message"


def test_context_includes_web_tool_results(services):
    database, settings, memory = services
    conversation_id = database.create_conversation()
    messages = ContextBuilder(database, settings, memory).build(
        conversation_id,
        "What is current?",
        tool_results=["Searched the web successfully. Example result https://example.com"],
    )
    assert "Searched the web successfully." in messages[0]["content"]
    assert "https://example.com" in messages[0]["content"]


def test_current_user_message_is_not_duplicated(services):
    database, settings, memory = services
    conversation_id = database.create_conversation()
    database.add_message(conversation_id, "user", "same turn")
    messages = ContextBuilder(database, settings, memory).build(conversation_id, "same turn")
    assert [item["content"] for item in messages].count("same turn") == 1


def test_context_includes_attachment_metadata_and_extracted_text(services):
    database, settings, memory = services
    conversation_id = database.create_conversation()
    database.add_message(
        conversation_id,
        "user",
        "Review this",
        attachments=[
            {
                "name": "notes.txt",
                "path": "C:/private/path/notes.txt",
                "mime_type": "text/plain",
                "media_kind": "text",
                "size": 12,
                "parse_status": "text_extracted",
                "text_excerpt": "Useful extracted notes",
            }
        ],
    )

    messages = ContextBuilder(database, settings, memory).build(
        conversation_id, "What was in my attachment?"
    )
    history = "\n".join(item["content"] for item in messages)
    assert "notes.txt" in history
    assert "Useful extracted notes" in history
    assert "C:/private/path" not in history
