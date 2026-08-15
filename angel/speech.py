from __future__ import annotations

import base64
import logging
import os
import re
import shutil
import subprocess
import threading
from pathlib import Path


MAX_SPEECH_CHARS = 24_000


def clean_text_for_speech(text: str) -> str:
    """Turn common Markdown into calmer spoken text and cap very long replies."""
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    cleaned = re.sub(r"```(?:\w+)?\s*", "", cleaned)
    cleaned = cleaned.replace("```", "").replace("`", "")
    cleaned = re.sub(r"(?m)^\s{0,3}#{1,6}\s+", "", cleaned)
    cleaned = re.sub(r"(?m)^\s*[-*+]\s+", "", cleaned)
    cleaned = re.sub(r"(?m)^\s*\d+[.)]\s+", "", cleaned)
    cleaned = re.sub(r"https?://\S+", "link", cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    if len(cleaned) > MAX_SPEECH_CHARS:
        shortened = cleaned[:MAX_SPEECH_CHARS].rsplit(" ", 1)[0].rstrip()
        cleaned = (shortened or cleaned[:MAX_SPEECH_CHARS]).rstrip() + "…"
    return cleaned


def _encoded_command(script: str) -> str:
    return base64.b64encode(script.encode("utf-16-le")).decode("ascii")


LIST_VOICES_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
$OutputEncoding = [Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
Add-Type -AssemblyName System.Speech
$synth = [System.Speech.Synthesis.SpeechSynthesizer]::new()
try {
    foreach ($installed in $synth.GetInstalledVoices()) {
        if ($installed.Enabled) {
            [Console]::Out.WriteLine($installed.VoiceInfo.Name)
        }
    }
} finally {
    $synth.Dispose()
}
"""


SPEAK_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$synth = [System.Speech.Synthesis.SpeechSynthesizer]::new()
try {
    if (-not [string]::IsNullOrWhiteSpace($env:ANGEL_TTS_VOICE)) {
        $synth.SelectVoice($env:ANGEL_TTS_VOICE)
    }
    $rate = 0
    if ([int]::TryParse($env:ANGEL_TTS_RATE, [ref]$rate)) {
        $synth.Rate = [Math]::Max(-10, [Math]::Min(10, $rate))
    }
    $text = [Console]::In.ReadToEnd()
    if (-not [string]::IsNullOrWhiteSpace($text)) {
        $synth.Speak($text)
    }
} finally {
    $synth.Dispose()
}
"""


class WindowsSpeechService:
    """Local text-to-speech backed by voices already installed in Windows."""

    def __init__(
        self,
        logger: logging.Logger | None = None,
        powershell_path: str | Path | None = None,
    ) -> None:
        self.logger = logger or logging.getLogger("angel.speech")
        self.powershell_path = str(powershell_path or self._find_powershell() or "")
        self._lock = threading.Lock()
        self._process: subprocess.Popen[str] | None = None

    @staticmethod
    def _find_powershell() -> Path | None:
        system_root = Path(os.environ.get("SystemRoot", r"C:\Windows"))
        native = system_root / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
        if native.is_file():
            return native
        discovered = shutil.which("powershell.exe") or shutil.which("powershell")
        return Path(discovered) if discovered else None

    @staticmethod
    def _creation_flags() -> int:
        return int(getattr(subprocess, "CREATE_NO_WINDOW", 0))

    def list_voices(self, timeout: float = 8.0) -> list[str]:
        if not self.powershell_path:
            return []
        try:
            completed = subprocess.run(
                [
                    self.powershell_path,
                    "-NoLogo",
                    "-NoProfile",
                    "-NonInteractive",
                    "-EncodedCommand",
                    _encoded_command(LIST_VOICES_SCRIPT),
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                creationflags=self._creation_flags(),
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            self.logger.exception("Windows voice discovery failed")
            return []
        if completed.returncode != 0:
            self.logger.warning("Windows voice discovery returned code %s", completed.returncode)
            return []
        return list(dict.fromkeys(line.strip() for line in completed.stdout.splitlines() if line.strip()))

    def speak(self, text: str, voice_name: str = "", rate: int = 0) -> bool:
        spoken_text = clean_text_for_speech(text)
        if not spoken_text or not self.powershell_path:
            return False
        self.stop()
        environment = os.environ.copy()
        environment["ANGEL_TTS_VOICE"] = voice_name.strip()
        environment["ANGEL_TTS_RATE"] = str(max(-10, min(10, int(rate))))
        try:
            process = subprocess.Popen(
                [
                    self.powershell_path,
                    "-NoLogo",
                    "-NoProfile",
                    "-NonInteractive",
                    "-EncodedCommand",
                    _encoded_command(SPEAK_SCRIPT),
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=environment,
                creationflags=self._creation_flags(),
            )
        except OSError:
            self.logger.exception("Windows speech could not start")
            return False
        with self._lock:
            self._process = process
        try:
            # Allow roughly eight spoken characters per second, while preventing a
            # missing or busy audio device from leaving a worker stuck forever.
            timeout = max(30.0, min(1_800.0, len(spoken_text) / 8.0 + 15.0))
            _output, error = process.communicate(spoken_text, timeout=timeout)
            if process.returncode != 0:
                self.logger.warning(
                    "Windows speech returned code %s: %s",
                    process.returncode,
                    (error or "unknown error").strip()[:300],
                )
                return False
            return True
        except subprocess.TimeoutExpired:
            self.logger.warning("Windows speech timed out")
            try:
                process.terminate()
                process.communicate(timeout=2.0)
            except (OSError, subprocess.SubprocessError):
                try:
                    process.kill()
                except OSError:
                    pass
            return False
        except (OSError, subprocess.SubprocessError):
            self.logger.exception("Windows speech failed")
            return False
        finally:
            with self._lock:
                if self._process is process:
                    self._process = None

    def stop(self) -> None:
        with self._lock:
            process = self._process
            self._process = None
        if process is not None and process.poll() is None:
            try:
                process.terminate()
            except OSError:
                pass

    def close(self) -> None:
        self.stop()
