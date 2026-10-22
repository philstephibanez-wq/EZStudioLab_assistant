"""Public web search for each PROFILE item, without paid API keys.
Search and read original webpages. A search result is not a musical verdict.
"""
from __future__ import annotations
import re
from profile_final_verifier import final_assertions
from profile_public_web import search, fetch_document
from profile_live_evidence import evaluate_live_documents

TERMS={"tempo":"BPM tempo","meter":"time signature meter","key":"musical key tonality","genre":"genre style","lead_vocal":"lead vocals singer","backing_vocals":"backing vocals","choir":"choir choral vocals","vocal_harmonies":"vocal harmonies"}

def research_each_assertion(row, identity, **unused):
    title=str(identity.get("title") or "").strip()
    artist=str(identity.get("artist") or "").strip()
    items=[]
    for assertion in final_assertions(row):
        key=assertion["key"]
        item={"key":key,"value":assertion["value"],"status":"not_searched","citation_urls":[],
              "documents":[],"eligible_for_verdict":False}
        if not title:
            item["status"]="identity_unavailable"
            items.append(item)
            continue
        topic=TERMS.get(key,"instrument "+assertion["value"] if key.startswith("instrument:") else key)
        query='"'+title+'" "'+artist+'" '+topic if artist else '"'+title+'" '+topic
        item["query"]=query
        try:
            hits=search(query,max_results=8)
            for hit in hits:
                url=hit.get("url")
                if not url:continue
                doc={"url":url,"title":hit.get("title"),"snippet":hit.get("snippet"),
                     "status":"unread"}
                try:
                    source=fetch_document(url)
                    doc["status"]=source.get("status")
                    if source.get("status")=="read":
                        doc["text"]=source.get("text","")[:8000]
                except Exception as exc:
                    doc["status"]="read_error"
                    doc["error_type"]=type(exc).__name__
                item["documents"].append(doc)
                item["citation_urls"].append(url)
            item["status"]="documents_read" if any(d.get("status")=="read" for d in item["documents"]) else (
                "no_results" if not hits else "sources_unreadable")
        except Exception as exc:
            item["status"]="error"
            item["reason"]=type(exc).__name__+":"+str(exc)[:180]
        item["evidence_review"]=evaluate_live_documents(assertion,identity,item["documents"])
        items.append(item)
    return {"status":"completed" if items else "no_assertions",
            "searched":len(items),"items":items,
            "search_provider":"public_web_no_api_key","automatic_verdicts":False}
