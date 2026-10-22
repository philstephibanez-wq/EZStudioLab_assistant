"""Keyless public web discovery for PROFILE; real HTTP only, no generated sources.

Bing publishes an RSS search feed. Its availability and commercial usage
conditions must be independently reviewed before SaaS operation.
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

def search(query,max_results=10):
    endpoint="https://www.bing.com/search?"+urllib.parse.urlencode({"q":query,"format":"rss"})
    raw,_=_fetch(endpoint)
    root=ET.fromstring(raw)
    results=[]
    for item in root.findall(".//item"):
        url=_url(item.findtext("link"))
        if not url:continue
        results.append({"url":url,"title":html.unescape(item.findtext("title") or "")[:250],
             "snippet":html.unescape(re.sub("<[^>]+>"," ",item.findtext("description") or ""))[:600]})
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
