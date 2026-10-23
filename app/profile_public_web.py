"""Public-web research through a self-hosted SearXNG JSON endpoint.

No commercial search API, mock responses, public HTML scraping or RSS fallback.
"""
from __future__ import annotations
import html
import ipaddress
import json
import os
import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser

class _VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts=[]
        self.hidden=0
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style","noscript"):
            self.hidden+=1
    def handle_endtag(self,tag):
        if tag in ("script","style","noscript") and self.hidden:
            self.hidden-=1
    def handle_data(self,data):
        if not self.hidden and data.strip():
            self.parts.append(data.strip())

def _url(value):
    try:
        p=urllib.parse.urlsplit(str(value))
        if p.scheme!="https" or not p.hostname or p.username or p.password:
            return None
        if p.hostname.lower() in ("localhost",) or p.hostname.lower().endswith(".local"):
            return None
        try:
            if not ipaddress.ip_address(p.hostname).is_global:
                return None
        except ValueError:
            pass
        return p.geturl()
    except (TypeError,ValueError):
        return None

def _endpoint():
    raw=os.environ.get("EZS_SEARXNG_URL","").strip()
    if not raw:
        raise RuntimeError("SEARXNG_NOT_CONFIGURED")
    p=urllib.parse.urlsplit(raw)
    if p.scheme not in ("http","https") or not p.hostname or p.username or p.password:
        raise RuntimeError("SEARXNG_ENDPOINT_INVALID")
    if p.path not in ("","/") or p.query or p.fragment:
        raise RuntimeError("SEARXNG_ENDPOINT_MUST_BE_BASE_URL")
    return raw.rstrip("/")

def search(query,max_results=10):
    endpoint=_endpoint()+"/search?"+urllib.parse.urlencode({
        "q":query,"format":"json","categories":"general","language":"en-US"})
    request=urllib.request.Request(endpoint,headers={
        "Accept":"application/json","User-Agent":"EZStudioLabAssistant/1.7"})
    try:
        with urllib.request.urlopen(request,timeout=20) as response:
            if response.status!=200:
                raise RuntimeError("SEARXNG_HTTP_"+str(response.status))
            data=json.loads(response.read(1_500_000).decode("utf-8"))
    except Exception as exc:
        raise RuntimeError("SEARXNG_SEARCH_FAILED:"+type(exc).__name__) from exc
    if not isinstance(data,dict) or not isinstance(data.get("results"),list):
        raise RuntimeError("SEARXNG_INVALID_RESPONSE")
    results=[]
    seen=set()
    for item in data["results"]:
        if not isinstance(item,dict):
            continue
        link=_url(item.get("url"))
        if not link or link in seen:
            continue
        seen.add(link)
        results.append({"url":link,
            "title":html.unescape(str(item.get("title") or ""))[:250],
            "snippet":html.unescape(re.sub(r"<[^>]+>"," ",
                       str(item.get("content") or "")))[:600],
            "search_provider":"searxng"})
        if len(results)>=max_results:
            break
    return results

def fetch_document(url):
    safe=_url(url)
    if not safe:
        return {"status":"unsafe_url"}
    request=urllib.request.Request(safe,headers={"Accept":"text/html,text/plain",
        "User-Agent":"EZStudioLabAssistant/1.7"})
    try:
        with urllib.request.urlopen(request,timeout=14) as response:
            final=_url(response.geturl())
            kind=str(response.headers.get("Content-Type") or "").lower()
            if not final:
                return {"status":"unsafe_redirect"}
            if not ("text/html" in kind or "text/plain" in kind):
                return {"status":"unsupported_content_type"}
            raw=response.read(600_001)
            if len(raw)>600_000:
                return {"status":"document_too_large"}
        parser=_VisibleText()
        parser.feed(raw.decode("utf-8","replace"))
        body=re.sub(r"\s+"," "," ".join(parser.parts)).strip()
        return {"status":"read","url":final,"text":body[:18000],
                "char_count":len(body)}
    except Exception as exc:
        return {"status":"read_error","reason":type(exc).__name__}
