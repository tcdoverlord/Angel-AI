from .tools import looks_weather,looks_datetime
class Router:
    def plan(self,text,location):
        w,t=looks_weather(text),looks_datetime(text)
        if w and t:return [("current_datetime",{}),("current_weather",{"location":location})]
        if w:return [("current_weather",{"location":location})]
        if t:return [("current_datetime",{})]
        return []
