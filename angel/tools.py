import json,re
from dataclasses import dataclass
from datetime import datetime
from urllib.request import urlopen
from urllib.parse import quote
@dataclass
class ToolResult: name:str; content:str; success:bool=True
def current_datetime():
    n=datetime.now().astimezone()
    return ToolResult("current_datetime",f"Local date: {n:%A, %B %d, %Y}\nLocal time: {n:%I:%M:%S %p}\nTimezone: {n.tzname() or n.tzinfo}")
def weather(location):
    try:
        g=json.loads(urlopen(f"https://geocoding-api.open-meteo.com/v1/search?name={quote(location)}&count=1&language=en&format=json",timeout=12).read())
        p=(g.get("results") or [None])[0]
        if not p:return ToolResult("current_weather",f"Location not found: {location}",False)
        lat,lon=p["latitude"],p["longitude"]
        d=json.loads(urlopen(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m&temperature_unit=fahrenheit&wind_speed_unit=mph&timezone=auto",timeout=12).read())["current"]
        desc={0:"Clear sky",1:"Mainly clear",2:"Partly cloudy",3:"Overcast"}.get(d["weather_code"],f"Weather code {d['weather_code']}")
        return ToolResult("current_weather",f"Weather for {p['name']}, {p.get('admin1','')}: {desc}\nTemperature: {d['temperature_2m']}°F (feels like {d['apparent_temperature']}°F)\nHumidity: {d['relative_humidity_2m']}%\nWind: {d['wind_speed_10m']} mph")
    except Exception as e:return ToolResult("current_weather",f"Weather unavailable: {e}",False)
def looks_weather(t): return bool(re.search(r"\b(weather|forecast|temperature|conditions)\b",t,re.I))
def looks_datetime(t): return bool(re.search(r"\b(date|time|today|what day)\b",t,re.I))
