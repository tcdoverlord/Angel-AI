from __future__ import annotations

import logging

from angel.brain import AngelBrain
from angel.context import ContextBuilder
from angel.creator import AceStepBackend, ComfyUIBackend, CreatorLibrary, ModelRouter
from angel.database import Database
from angel.knowledge import KnowledgeService
from angel.memory import MemoryService
from angel.ollama_client import OllamaError
from angel.paths import installation_layout
from angel.personality import ANGEL_PERSONALITY
from angel.projects import ProjectService
from angel.recommendations import RecommendationService
from angel.search import SearchService
from angel.settings import SettingsService
from angel.tools import create_tool_registry


class OfflineSearchProvider:
    calls = 0

    def search(self, query, limit=5):
        self.calls += 1
        raise AssertionError("External search must not run in Offline mode")


class LocalModel:
    def __init__(self, response="Local help works without external internet."):
        self.response = response
        self.messages = []

    @staticmethod
    def is_local_url(_url):
        return True

    def chat(self, base_url, model, messages):
        self.messages.append(messages)
        return self.response


def make_full(tmp_path):
    layout = installation_layout(tmp_path / "Angel")
    database = Database(layout.database, logging.getLogger("test.local-first"))
    settings = SettingsService(database)
    memory = MemoryService(database, settings)
    projects = ProjectService(database, settings)
    knowledge = KnowledgeService(database, settings, layout)
    search = SearchService(OfflineSearchProvider())
    local_model = LocalModel()
    tools = create_tool_registry(database, settings, memory, search, projects=projects, knowledge=knowledge)
    context = ContextBuilder(database, settings, memory, projects=projects, knowledge=knowledge)
    brain = AngelBrain(database, settings, context, tools, local_model, RecommendationService(database, settings))
    return layout, database, settings, memory, projects, knowledge, local_model, tools, brain


def test_offline_mode_blocks_external_search_but_local_chat_and_memory_work(tmp_path):
    _layout, database, settings, memory, _projects, _knowledge, local_model, _tools, brain = make_full(tmp_path)
    settings.update(connectivity_mode="Offline")
    conversation_id = database.create_conversation()

    creative = brain.respond("Help me write a song about rebuilding", conversation_id)
    current = brain.respond("What happened in the news today?", conversation_id)
    memory.add("I prefer practical explanations.", "preference")

    assert creative.local_ai_available is True
    assert current.local_ai_available is True
    assert len(local_model.messages) == 2
    assert memory.search("practical")
    assert not creative.sources and not current.sources


def test_personality_and_layered_context_preserve_identity_truth_and_preferences(tmp_path):
    _layout, database, settings, memory, projects, _knowledge, local_model, _tools, brain = make_full(tmp_path)
    settings.update(
        technical_level="Plain language first",
        formatting_preference="Natural paragraphs",
        workflow_preferences="Treat software as a complete product",
    )
    project = projects.create("Angel AI", "One persistent personal AI")
    projects.update(int(project["id"]), current_state="Improving personality and context")
    projects.set_active(int(project["id"]))
    memory.add("The user wants Angel to explain technical ideas simply.", "preference")
    conversation_id = database.create_conversation()

    brain.respond("Continue Angel and explain localhost", conversation_id)
    system = local_model.messages[0][0]["content"]

    assert "You are Angel" in ANGEL_PERSONALITY
    assert "Never pretend" in system
    assert "Plain language first" in system
    assert "Improving personality and context" in system
    assert "explain technical ideas simply" in system
    assert "underlying engine" in system


def test_model_identity_opening_is_removed_without_rewriting_real_answer():
    response = AngelBrain._clean_response(
        "As a Llama model, I can explain the tradeoff: 1080p60 is smoother for motion."
    )
    assert response.startswith("I can explain the tradeoff")
    assert "1080p60" in response


def test_creator_backends_fail_gracefully_and_library_metadata_persists(tmp_path):
    layout = installation_layout(tmp_path / "Angel")
    database = Database(layout.database)
    settings = SettingsService(database)
    settings.update(comfyui_url="http://127.0.0.1:9", acestep_url="http://127.0.0.1:9")
    library = CreatorLibrary(database)
    images = ComfyUIBackend(settings, layout, library)
    music = AceStepBackend(settings, layout, library)
    router = ModelRouter(settings, images, music)

    statuses = router.statuses(True, [settings.get().model])
    item = library.add("lyrics", "Local Song", "write lyrics", "", "Angel Chat", settings.get().model, 42, {"genre": "rock"})

    assert next(status for status in statuses if status.role == "Image AI").installed is False
    assert next(status for status in statuses if status.role == "Music AI").installed is False
    assert library.get(int(item["id"]))["metadata"]["genre"] == "rock"
    assert database.integrity_check()[0] is True
