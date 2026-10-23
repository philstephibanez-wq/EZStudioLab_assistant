"""Keyless public web discovery for PROFILE; real HTTP only, no generated sources.
DuckDuckGo HTML is a public website, not a guaranteed or licensed search API.
"""
from __future__ import annotations
import html
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

class _VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts=[]
        self.hidden=0
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style","noscript"):self.hidden+=1
    def handle_endtag(self,tag):
        if tag in ("script","style","noscript") and self.hidden:self.hidden-=1
    def handle_data(self,data):
        if not self.hidden and data.strip():self.parts.append(data.strip())

def _url(url):
    try:
        p=urllib.parse.urlsplit(str(url))
        return p.geturl() if p.scheme=="https" and p.hostname and not p.username and not p.password else None
    except (ValueError,TypeError):
        return None

def _fetch(url,*,timeout=14,max_bytes=600000):
    req=urllib.request.Request(url,headers={"User-Agent":"EZStudioLabAssistant/1.6 (music citation research)","Accept":"application/rss+xml, text/html;q=0.9,*/*;q=0.5"})
    with urllib.request.urlopen(req,timeout=timeout) as response:
        if response.status!=200:raise ValueError("unexpected_http_status")
        content_type=response.headers.get("Content-Type","")
        return response.read(max_bytes+1)[:max_bytes],content_type

class _SearchResults(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results=[]
        self._target=None
        self._title=[]
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if tag=="a" and "result__a" in attrs.get("class","").split():
            self._target=attrs.get("href")
            self._title=[]
    def handle_data(self, data):
        if self._target is not None:
            self._title.append(data)
    def handle_endtag(self,tag):
        if tag=="a" and self._target is not None:
            target=self._target
            parsed=urllib.parse.urlsplit(urllib.parse.urljoin("https://html.duckduckgo.com/",target))
            if parsed.hostname and parsed.hostname.endswith("duckduckgo.com"):
                target=urllib.parse.parse_qs(parsed.query).get("uddg",[None])[0]
            link=_url(target)
            if link and urllib.parse.urlsplit(link).hostname not in ("duckduckgo.com","html.duckduckgo.com"):
                self.results.append({"url":link,"title":html.unescape(" ".join(self._title)).strip()[:250],"snippet":""})
            self._target=None
            self._title=[]

def search(query,max_results=10):
    """Discover real URLs from a public, keyless HTML search engine.

    Fail closed when the response cannot be parsed. No unrelated RSS fallback.
    """
    endpoint="https://html.duckduckgo.com/html/?"+urllib.parse.urlencode({"q":query,"kl":"us-en"})
    raw,kind=_fetch(endpoint)
    if "html" not in kind.lower():
        raise ValueError("search_engine_unexpected_content_type")
    parser=_SearchResults()
    parser.feed(raw.decode("utf-8","replace"))
    if not parser.results:
        raise ValueError("search_engine_no_parsable_results")
    seen=set()
    results=[]
    for hit in parser.results:
        if hit["url"] in seen:continue
        seen.add(hit["url"])
        results.append(hit)
        if len(results)>=max_results:break
    return results

def fetch_document(url):
    safe=_url(url)
    if not safe:return {"status":"unsafe_url"}
    raw,kind=_fetch(safe)
    if "text/html" not in kind.lower() and "text/plain" not in kind.lower():
        return {"status":"unsupported_content_type"}
    parser=_VisibleText()
    parser.feed(raw.decode("utf-8","replace"))
    body=re.sub(r"\s+"," "," ".join(parser.parts)).strip()
    return {"status":"read","url":safe,"text":body[:18000],"char_count":len(body)}
