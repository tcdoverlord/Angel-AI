import json
import os
import shutil
import subprocess
import threading
import time
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

class OllamaError(RuntimeError): pass

class OllamaClient:
    def __init__(self, base_url, timeout=180):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._serve_process = None
        self._lock = threading.Lock()

    def online(self):
        try:
            with urlopen(self.base_url + '/api/tags', timeout=2) as r:
                return r.status == 200
        except Exception:
            return False

    def executable(self):
        return shutil.which('ollama') or shutil.which('ollama.exe')

    def start_local(self):
        """Start Ollama locally if it is installed and not already serving."""
        if self.online():
            return True, 'Ollama is already online.'
        exe = self.executable()
        if not exe:
            common = os.path.expandvars(r'%LOCALAPPDATA%\Programs\Ollama\ollama.exe')
            if os.path.isfile(common): exe = common
        if not exe:
            return False, 'Ollama is not installed or ollama.exe could not be found.'
        with self._lock:
            if not self.online():
                try:
                    env = os.environ.copy()
                    env.setdefault('OLLAMA_HOST', '127.0.0.1:11434')
                    creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
                    self._serve_process = subprocess.Popen(
                        [exe, 'serve'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        stdin=subprocess.DEVNULL, env=env, creationflags=creationflags
                    )
                except Exception as e:
                    return False, f'Could not start Ollama: {e}'
        for _ in range(30):
            if self.online(): return True, 'Ollama is online.'
            time.sleep(.25)
        return False, 'Ollama did not become ready on http://127.0.0.1:11434.'

    def models(self):
        try:
            with urlopen(self.base_url + '/api/tags', timeout=5) as r:
                return [x.get('name') for x in json.loads(r.read()).get('models', [])]
        except Exception:
            return []

    def chat(self, model, messages):
        payload={'model':model,'messages':messages,'stream':False}
        req=Request(self.base_url+'/api/chat',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
        try:
            with urlopen(req,timeout=self.timeout) as r:
                data=json.loads(r.read())
            return data.get('message',{}).get('content','').strip()
        except (HTTPError,URLError,TimeoutError,OSError) as e:
            raise OllamaError(str(e)) from e
