from __future__ import annotations

import time
import tkinter as tk
import threading
from types import SimpleNamespace

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
        self.calls = []

    def respond(self, *args, **kwargs):
        mode = kwargs.get("mode") if "mode" in kwargs else args[2]
        attachments = kwargs.get("attachments") if "attachments" in kwargs else args[4]
        self.modes.append(mode)
        self.calls.append({"text": args[0], "mode": mode, "attachments": attachments})
        return BrainResponse("unused", local_ai_available=False)


class FakeSpeech:
    def __init__(self):
        self.calls = []
        self.stop_count = 0

    def list_voices(self):
        return ["Test Windows Voice"]

    def speak(self, text, voice_name="", rate=0):
        self.calls.append((text, voice_name, rate))
        return True

    def stop(self):
        self.stop_count += 1

    def close(self):
        self.stop()


def test_sources_are_visibly_labeled_and_clickable(services, monkeypatch, tmp_path):
    database, settings, memory = services
    root = tk.Tk()
    root.withdraw()
    brain = UnusedBrain()
    ollama = WaitingOllama()
    speech = FakeSpeech()
    ui = AngelUI(root, database, settings, memory, brain, ollama, speech=speech)
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

        note = tmp_path / "note.txt"
        note.write_text("Use this attachment text.", encoding="utf-8")
        media = tmp_path / "recording.anymedia"
        media.write_bytes(b"\x00\x01media")
        monkeypatch.setattr(
            "angel.ui.filedialog.askopenfilenames",
            lambda **kwargs: (str(note), str(media)),
        )
        ui.upload_files()
        assert len(ui.pending_attachments) == 2
        ui.input_box.insert("1.0", "Review these files")
        assert ui._send_on_enter(SimpleNamespace(state=0)) == "break"
        deadline = time.monotonic() + 2
        while ui.busy and time.monotonic() < deadline:
            root.update()
            time.sleep(0.01)
        assert brain.calls[-1]["text"] == "Review these files"
        assert [item["name"] for item in brain.calls[-1]["attachments"]] == [
            "note.txt",
            "recording.anymedia",
        ]
        assert ui.pending_attachments == []
        assert "note.txt" in ui.chat.get("1.0", "end")

        calls_before_shift_enter = len(brain.calls)
        ui.input_box.insert("1.0", "Keep editing")
        assert ui._send_on_enter(SimpleNamespace(state=0x0001)) is None
        assert len(brain.calls) == calls_before_shift_enter
        ui.input_box.delete("1.0", "end")

        for mode in QUICK_ACTIONS:
            ui.send_quick_action(mode)
            deadline = time.monotonic() + 2
            while ui.busy and time.monotonic() < deadline:
                root.update()
                time.sleep(0.01)
            assert ui.busy is False
        assert [mode for mode in brain.modes if mode] == list(QUICK_ACTIONS)
        deadline = time.monotonic() + 2
        while ui.speech_future is not None and time.monotonic() < deadline:
            root.update()
            time.sleep(0.01)
        assert speech.calls
        assert speech.calls[-1] == ("unused", "", 0)

        settings.update(read_aloud_enabled=False)
        ui.auto_read_var.set(False)
        calls_before_manual_read = len(speech.calls)
        ui.read_last_reply()
        deadline = time.monotonic() + 2
        while ui.speech_future is not None and time.monotonic() < deadline:
            root.update()
            time.sleep(0.01)
        assert len(speech.calls) == calls_before_manual_read + 1
        ui.stop_speaking()
        assert speech.stop_count > 0

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
