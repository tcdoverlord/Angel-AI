import json
from urllib.request import Request,urlopen
class OllamaError(RuntimeError): pass
class OllamaClient:
    def __init__(self,base_url,timeout=120): self.base_url=base_url.rstrip("/"); self.timeout=timeout
    def chat(self,model,messages):
        req=Request(self.base_url+"/api/chat",data=json.dumps({"model":model,"messages":messages,"stream":False}).encode(),headers={"Content-Type":"application/json"})
        try:
            with urlopen(req,timeout=self.timeout) as r: return json.loads(r.read())["message"]["content"].strip()
        except Exception as e: raise OllamaError(str(e)) from e
