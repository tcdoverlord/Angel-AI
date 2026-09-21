
"""Bounded web search service used by Angel Platform 3.3.1."""
from dataclasses import dataclass, asdict
from html.parser import HTMLParser
from urllib.parse import quote, urljoin
from urllib.request import Request, urlopen
import re

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str = ""

    def to_dict(self):
        return asdict(self)

class _Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results=[]; self._current=None; self._capture=None
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=="a" and "result__a" in a.get("class",""):
            self._current={"title":"","url":urljoin("https://duckduckgo.com",a.get("href",""))}
            self._capture="title"
        elif self._current and tag=="a" and "result__snippet" in a.get("class",""):
            self._capture="snippet"
        elif self._current and tag=="a" and "result__url" in a.get("class",""):
            self._capture="url"
    def handle_data(self,data):
        if self._current and self._capture:
            self._current[self._capture]=self._current.get(self._capture,"")+" "+data.strip()
    def handle_endtag(self,tag):
        if tag=="a" and self._current and self._capture=="title":
            self._capture=None
        if tag=="a" and self._current and self._capture in ("snippet","url"):
            self._capture=None
            if self._current.get("title"):
                self.results.append(self._current); self._current=None

def search_web(query: str, limit: int=5):
    query=(query or "").strip()
    if not query: return []
    request=Request("https://html.duckduckgo.com/html/?q="+quote(query),
                    headers={"User-Agent":"AngelPlatform/3.3.1"})
    with urlopen(request, timeout=12) as response:
        parser=_Parser(); parser.feed(response.read().decode("utf-8","ignore"))
    seen=set(); output=[]
    for item in parser.results:
        if item["url"] in seen: continue
        seen.add(item["url"])
        output.append(SearchResult(item["title"].strip(),item["url"],item.get("snippet","").strip()))
        if len(output)>=max(1,min(limit,10)): break
    return output
