import threading

class Voice:
    def __init__(self,enabled=True,rate=180):
        self.enabled=enabled; self.rate=rate; self._lock=threading.Lock(); self._engine=None; self._thread=None; self._stop=False; self.last_text=''
    def _run(self,text):
        try:
            import pyttsx3
            engine=pyttsx3.init(); self._engine=engine; engine.setProperty('rate',self.rate)
            with self._lock: stopped=self._stop
            if not stopped: engine.say(text); engine.runAndWait()
        except Exception:
            pass
        finally:
            try:
                if self._engine: self._engine.stop()
            except Exception: pass
            self._engine=None
    def speak(self,text):
        if not self.enabled or not text.strip(): return False
        self.stop(); self.last_text=text; self._stop=False
        self._thread=threading.Thread(target=self._run,args=(text,),daemon=True); self._thread.start(); return True
    def replay(self): return self.speak(self.last_text) if self.last_text else False
    def stop(self):
        self._stop=True
        try:
            if self._engine: self._engine.stop()
        except Exception: pass
    def speaking(self): return bool(self._thread and self._thread.is_alive())
