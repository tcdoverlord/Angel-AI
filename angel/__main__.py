from .config import Config
from .ollama import OllamaClient
from .brain import AngelBrain
from .cli import run
if __name__=="__main__":
    c=Config.from_env(); run(AngelBrain(OllamaClient(c.ollama_url,c.timeout),c.model,c.location))
