from datetime import datetime
import json,re
from urllib.parse import quote
from urllib.request import urlopen

def current_datetime():
    n=datetime.now().astimezone(); return f"Local date: {n:%A, %B %d, %Y}\nLocal time: {n:%I:%M:%S %p}\nTimezone: {n.tzname() or n.tzinfo}"

def weather(location):
    try:
        with urlopen("https://geocoding-api.open-meteo.com/v1/search?name="+quote(location)+"&count=1&language=en&format=json",timeout=12) as r: g=json.loads(r.read())
        p=(g.get("results") or [])[0]; lat,lon=p["latitude"],p["longitude"]
        u=f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m&temperature_unit=fahrenheit&wind_speed_unit=mph&timezone=auto"
        with urlopen(u,timeout=12) as r: c=json.loads(r.read())["current"]
        codes={0:"Clear sky",1:"Mainly clear",2:"Partly cloudy",3:"Overcast",45:"Fog",51:"Light drizzle",61:"Rain",71:"Snow",80:"Rain showers",95:"Thunderstorm"}
        return f"Weather for {p.get('name',location)}: {codes.get(c.get('weather_code'),'Current conditions')}\nTemperature: {c.get('temperature_2m')}°F (feels like {c.get('apparent_temperature')}°F)\nHumidity: {c.get('relative_humidity_2m')}%\nWind: {c.get('wind_speed_10m')} mph"
    except Exception as e: return f"Weather unavailable: {e}"
