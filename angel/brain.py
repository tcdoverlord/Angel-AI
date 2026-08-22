from .router import Router
from .tools import current_datetime,weather
class AngelBrain:
    def __init__(self,client,model,location): self.client=client; self.model=model; self.location=location; self.router=Router()
    def respond(self,text):
        plans=self.router.plan(text,self.location)
        if plans:
            out=[]
            for name,args in plans: out.append((current_datetime() if name=="current_datetime" else weather(args["location"])).content)
            return "\n\n".join(out)
        return self.client.chat(self.model,[{"role":"system","content":"You are Angel AI, a concise local assistant. Never invent live facts."},{"role":"user","content":text}])
