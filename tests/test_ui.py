from __future__ import annotations

import time
import tkinter as tk
import threading

from angel.brain import BrainResponse
from angel.recommendations import QUICK_ACTIONS
from angel.ui import AngelUI


class WaitingOllama:
    def __init__(self):
        self.release = threading.Event()

    def check(self, base_url):
        self.release.wait(5)
        return False, []


class UnusedBrain:
    def __init__(self):
        self.modes = []

    def respond(self, *args, **kwargs):
        self.modes.append(kwargs.get("mode") if "mode" in kwargs else args[2])
        return BrainResponse("unused", local_ai_available=False)


def test_sources_are_visibly_labeled_and_clickable(services, monkeypatch):
    database, settings, memory = services
    root = tk.Tk()
    root.withdraw()
    brain = UnusedBrain()
    ollama = WaitingOllama()
    ui = AngelUI(root, database, settings, memory, brain, ollama)
    try:
        ui.chat.configure(state="normal")
        ui.chat.delete("1.0", "end")
        ui._insert_message(
            "assistant",
            "A verified answer.",
            [
                {
                    "title": "Verified Source",
                    "url": "https://example.com/current",
                    "domain": "example.com",
                    "snippet": "Current information",
                }
            ],
        )
        rendered = ui.chat.get("1.0", "end")
        source_tags = [
            name
            for name in ui.chat.tag_names()
            if name.startswith("source_") and name.removeprefix("source_").isdigit()
        ]
        assert "Searched the web · 1 sources" in rendered
        assert "Verified Source — example.com" in rendered
        assert source_tags
        binding = ui.chat.tk.call(
            ui.chat._w, "tag", "bind", source_tags[0], "<Button-1>"
        )
        assert binding
        for mode in QUICK_ACTIONS:
            ui.send_quick_action(mode)
            deadline = time.monotonic() + 2
            while ui.busy and time.monotonic() < deadline:
                root.update()
                time.sleep(0.01)
            assert ui.busy is False
        assert brain.modes == list(QUICK_ACTIONS)

        delete_id = int(ui.current_conversation_id)
        database.add_message(delete_id, "user", "Delete this with the conversation")
        keep_id = database.create_conversation("Keep this conversation")
        ui.refresh_conversations(select_id=delete_id)
        monkeypatch.setattr("angel.ui.messagebox.askyesno", lambda *args, **kwargs: True)

        ui.delete_conversation()

        assert database.conversation_exists(delete_id) is False
        assert database.get_messages(delete_id) == []
        assert database.conversation_exists(keep_id) is True
        assert ui.current_conversation_id == keep_id

        ui.delete_conversation()
        assert database.conversation_exists(keep_id) is False
        assert ui.current_conversation_id not in {delete_id, keep_id}
        assert database.conversation_exists(int(ui.current_conversation_id)) is True
    finally:
        started = time.monotonic()
        ui.close()
        assert time.monotonic() - started < 0.5
        ollama.release.set()
