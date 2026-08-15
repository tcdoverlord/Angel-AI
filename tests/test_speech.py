from __future__ import annotations

from types import SimpleNamespace

from angel.speech import MAX_SPEECH_CHARS, WindowsSpeechService, clean_text_for_speech


class FakeProcess:
    def __init__(self, returncode=0):
        self.returncode = returncode
        self.received = ""
        self.terminated = False

    def communicate(self, text=None, timeout=None):
        if text is not None:
            self.received = text
        self.timeout = timeout
        return "", ""

    def poll(self):
        return None if not self.terminated else -15

    def terminate(self):
        self.terminated = True

    def kill(self):
        self.terminated = True


def test_speech_cleanup_handles_markdown_links_urls_and_length():
    text = "# Answer\n- Read [Angel docs](https://example.com/docs) at https://example.com.\n" + (
        "word " * 10_000
    )

    cleaned = clean_text_for_speech(text)

    assert "#" not in cleaned
    assert "[Angel docs]" not in cleaned
    assert "Angel docs" in cleaned
    assert "https://" not in cleaned
    assert len(cleaned) <= MAX_SPEECH_CHARS + 1


def test_windows_voice_discovery_returns_unique_names(monkeypatch):
    captured = {}

    def fake_run(arguments, **kwargs):
        captured["arguments"] = arguments
        captured["kwargs"] = kwargs
        return SimpleNamespace(returncode=0, stdout="Microsoft David\nMicrosoft Zira\nMicrosoft David\n")

    monkeypatch.setattr("angel.speech.subprocess.run", fake_run)
    speech = WindowsSpeechService(powershell_path="powershell.exe")

    assert speech.list_voices() == ["Microsoft David", "Microsoft Zira"]
    assert "-EncodedCommand" in captured["arguments"]
    assert captured["kwargs"].get("shell", False) is False


def test_speech_text_uses_standard_input_and_stop_terminates(monkeypatch):
    processes = []

    def fake_popen(arguments, **kwargs):
        process = FakeProcess()
        process.arguments = arguments
        process.kwargs = kwargs
        processes.append(process)
        return process

    monkeypatch.setattr("angel.speech.subprocess.Popen", fake_popen)
    speech = WindowsSpeechService(powershell_path="powershell.exe")
    unsafe_text = "Hello; Remove-Item C:\\important"

    assert speech.speak(unsafe_text, "Microsoft Zira", 3) is True
    assert processes[0].received == unsafe_text
    assert unsafe_text not in " ".join(processes[0].arguments)
    assert processes[0].kwargs["env"]["ANGEL_TTS_VOICE"] == "Microsoft Zira"
    assert processes[0].kwargs["env"]["ANGEL_TTS_RATE"] == "3"

    active = FakeProcess()
    speech._process = active
    speech.stop()
    assert active.terminated is True


def test_speech_settings_are_persisted_and_rate_is_bounded(services):
    _database, settings, _memory = services

    defaults = settings.get()
    assert defaults.read_aloud_enabled is True
    assert defaults.voice_name == ""
    assert defaults.speech_rate == 0

    updated = settings.update(
        read_aloud_enabled=False,
        voice_name="Microsoft David Desktop",
        speech_rate=99,
    )

    assert updated.read_aloud_enabled is False
    assert updated.voice_name == "Microsoft David Desktop"
    assert updated.speech_rate == 10
