from dataclasses import dataclass
import os
@dataclass
class Config:
    ollama_url:str="http://127.0.0.1:11434"; model:str="qwen3"; location:str="Indianapolis, IN"; timeout:float=120
    @classmethod
    def from_env(cls):
        return cls(os.getenv("ANGEL_OLLAMA_URL",cls.ollama_url),os.getenv("ANGEL_MODEL",cls.model),os.getenv("ANGEL_LOCATION",cls.location))
