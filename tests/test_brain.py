from __future__ import annotations

from angel.brain import AngelBrain
from angel.context import ContextBuilder
from angel.ollama_client import OllamaError
from angel.recommendations import RecommendationService
from angel.search import SearchResult, SearchService
from angel.tools import create_tool_registry


class SequenceOllama:
    def __init__(self, responses):
        self.responses = list(responses)
        self.messages = []

    def chat(self, base_url, model, messages):
        self.messages.append(messages)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class StaticSearch:
    def search(self, query, limit=5):
        return [
            {
                "title": "Current source",
                "url": "https://example.com/current",
                "snippet": "Verified current information",
            }
        ]


def make_brain(services, ollama):
    database, settings, memory = services
    search = SearchService(StaticSearch())
    tools = create_tool_registry(database, settings, memory, search)
    recommendations = RecommendationService(database, settings)
    return AngelBrain(
        database,
        settings,
        ContextBuilder(database, settings, memory),
        tools,
        ollama,
        recommendations,
    )


def test_brain_uses_search_and_persists_real_sources(services):
    database, _settings, _memory = services
    conversation_id = database.create_conversation()
    ollama = SequenceOllama(["Here is the verified current answer."])
    brain = make_brain(services, ollama)

    response = brain.respond("Search the web for current information", conversation_id)

    assert response.sources[0]["url"] == "https://example.com/current"
    saved = database.get_messages(conversation_id)[-1]
    assert saved["sources"] == response.sources
    assert "TRUST AND PROVENANCE BOUNDARY" in ollama.messages[0][0]["content"]


def test_brain_plans_combined_date_and_time_request(services):
    database, _settings, _memory = services
    conversation_id = database.create_conversation()
    ollama = SequenceOllama(["The current date and time are available."])
    brain = make_brain(services, ollama)

    response = brain.respond("What time and date is it?", conversation_id)

    assert response.tool_calls == 1
    assert "Local date:" in ollama.messages[0][0]["content"]
    assert "Local time:" in ollama.messages[0][0]["content"]

def test_brain_enforces_three_tool_calls(services):
    database, _settings, _memory = services
    conversation_id = database.create_conversation()
    request = 'ANGEL_TOOL_REQUEST {"name":"current_datetime","arguments":{}}'
    ollama = SequenceOllama([request, request, request, request])
    brain = make_brain(services, ollama)

    response = brain.respond("Use tools if necessary", conversation_id)

    assert response.tool_calls == 1
    assert "repeated the same tool request" in response.content


def test_brain_rejects_malformed_model_tool_output(services):
    database, _settings, _memory = services
    conversation_id = database.create_conversation()
    brain = make_brain(services, SequenceOllama(["ANGEL_TOOL_REQUEST not-json"]))

    response = brain.respond("Try a tool", conversation_id)

    assert "did not run anything" in response.content


def test_brain_stays_useful_when_ollama_is_offline(services):
    database, _settings, _memory = services
    conversation_id = database.create_conversation()
    brain = make_brain(services, SequenceOllama([OllamaError("offline")]))

    response = brain.respond("Hello", conversation_id)

    assert response.local_ai_available is False
    assert "conversation is saved" in response.content


def test_explicit_memory_is_saved_even_if_ollama_is_offline(services):
    database, _settings, memory = services
    conversation_id = database.create_conversation()
    brain = make_brain(services, SequenceOllama([OllamaError("offline")]))

    response = brain.respond("Remember that I prefer purple", conversation_id)

    assert "safe tool completed" in response.content
    assert memory.search("purple")


def test_brain_accepts_attachment_only_message_without_claiming_file_access(services):
    database, _settings, _memory = services
    conversation_id = database.create_conversation()
    ollama = SequenceOllama(["I can see the file metadata, but its content was not parsed."])
    brain = make_brain(services, ollama)
    attachment = {
        "name": "clip.mp4",
        "path": "C:/private/videos/clip.mp4",
        "mime_type": "video/mp4",
        "media_kind": "video",
        "size": 1024,
        "parse_status": "metadata_only",
        "text_excerpt": "",
    }

    response = brain.respond("", conversation_id, attachments=[attachment])

    assert response.content
    prompt = "\n".join(item["content"] for item in ollama.messages[0])
    assert "clip.mp4" in prompt
    assert "metadata only; content not parsed" in prompt
    assert "C:/private/videos" not in prompt
    saved = database.get_messages(conversation_id)[0]
    assert saved["content"] == "Uploaded file"
    assert saved["attachments"] == [attachment]
