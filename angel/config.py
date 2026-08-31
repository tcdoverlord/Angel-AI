from dataclasses import dataclass
from pathlib import Path
import json, os, sys

@dataclass
class Config:
    ollama_url: str = "http://127.0.0.1:11434"
    model: str = "qwen3"
    location: str = "Indianapolis, IN"
    timeout: float = 180.0
    voice_enabled: bool = True
    speech_rate: int = 180
    theme: str = "dark"
    mode: str = "companion"
    knowledge_path: str = ""
    root: Path = Path(__file__).resolve().parents[1]

    @classmethod
    def from_env(cls):
        c=cls(
            ollama_url=os.getenv("ANGEL_OLLAMA_URL",cls.ollama_url),
            model=os.getenv("ANGEL_MODEL",cls.model),
            location=os.getenv("ANGEL_LOCATION",cls.location),
            timeout=float(os.getenv("ANGEL_TIMEOUT",cls.timeout)),
            voice_enabled=os.getenv("ANGEL_VOICE","1").lower() not in {"0","false","no"},
            speech_rate=int(os.getenv("ANGEL_SPEECH_RATE",cls.speech_rate)),
            knowledge_path=os.getenv("ANGEL_KNOWLEDGE_PATH",""),
        )
        if getattr(sys,"frozen",False):
            # EXE is intentionally in <project>\dist.
            # Persistent state belongs in <project>\data, not PyInstaller temp.
            exe=Path(sys.executable).resolve()
            c.root=exe.parent.parent if exe.parent.name.lower()=="dist" else exe.parent
        data=c.root/"data"
        for sub in ("","knowledge","knowledge_backups","inbox","gpts","gpts/Angel","memory"):
            (data/sub).mkdir(parents=True,exist_ok=True)
        c.load_settings()
        if not c.knowledge_path:
            c.knowledge_path=str(data/"knowledge")
        return c

    @property
    def settings_path(self): return self.root/"data"/"settings.json"

    def load_settings(self):
        try:
            d=json.loads(self.settings_path.read_text(encoding="utf-8"))
            self.theme=d.get("theme",self.theme); self.mode=d.get("mode",self.mode)
            self.model=d.get("model",self.model); self.speech_rate=int(d.get("speech_rate",self.speech_rate))
            self.voice_enabled=bool(d.get("voice_enabled",self.voice_enabled))
            self.knowledge_path=d.get("knowledge_path",self.knowledge_path)
        except Exception: pass

    def save_settings(self):
        self.settings_path.parent.mkdir(parents=True,exist_ok=True)
        self.settings_path.write_text(json.dumps({
            "theme":self.theme,"mode":self.mode,"model":self.model,
            "speech_rate":self.speech_rate,"voice_enabled":self.voice_enabled,
            "knowledge_path":self.knowledge_path
        },indent=2),encoding="utf-8")
