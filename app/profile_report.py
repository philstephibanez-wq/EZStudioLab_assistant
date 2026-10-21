"""Export minimal, non-identifying PROFILE telemetry to the private reports repository.

Never export trace payloads, prompts, full model output, URLs, paths or tokens.
Requires an authenticated gh CLI on XPS; failures are non-fatal and observable.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

DEST = "philstephibanez-wq/EZStudio_Run_Reports"
DIMENSIONS = ("genre", "instrumentation", "lead_vocal", "backing_vocals", "choir")
SAFE_REASON = re.compile(r"^[a-z][a-z0-9_:-]{0,80}$")
SAFE_KEY = re.compile(r"^[a-z][a-z0-9_]{0,40}$")


def make_report(trace, outcome):
    events = []
    with trace.file.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                item = json.loads(line)
            except ValueError:
                continue
            if isinstance(item, dict):
                events.append(item)
    def last(name):
        return next((x.get("data") for x in reversed(events) if x.get("event") == name), None)
    sent = last("qwen.evidence.sent") or {}
    decoded = last("qwen.content.decoded") or {}
    validated = last("qwen.validated") or last("ai.review.normalized") or {}
    research = sent.get("public_research") if isinstance(sent, dict) else {}
    if not isinstance(research, dict):
        research = {}
    root_keys = sorted(k for k in decoded if SAFE_KEY.fullmatch(k)) if isinstance(decoded, dict) else []
    raw_dimensions = decoded.get("dimensions", decoded) if isinstance(decoded, dict) else {}
    dimension_keys = sorted(k for k in raw_dimensions if SAFE_KEY.fullmatch(k)) if isinstance(raw_dimensions, dict) else []
    checked = validated.get("dimensions") if isinstance(validated, dict) else {}
    if not isinstance(checked, dict):
        checked = {}
    dimensions = {}
    for name in DIMENSIONS:
        val = checked.get(name) if isinstance(checked.get(name), dict) else {}
        decision = val.get("decision")
        reason = val.get("reason")
        dimensions[name] = {
            "decision": decision if decision in ("match", "mismatch", "uncertain", "not_scored") else "unknown",
            "reason": reason if isinstance(reason, str) and SAFE_REASON.fullmatch(reason) else None,
            "evidence_count": len(val.get("evidence", [])) if isinstance(val.get("evidence"), list) else 0,
        }
    counts = {key: len(research.get(key, [])) if isinstance(research.get(key), list) else 0
              for key in ("recording_genres", "recording_credits", "wikipedia_quotes")}
    durations = {}
    for event in events:
        name = event.get("event")
        if name in ("research.duration", "ai.review.duration", "qwen.http.duration", "qwen.validate.duration"):
            us = event.get("duration_us")
            if isinstance(us, int) and 0 <= us <= 10**12:
                durations[name.replace(".", "_")] = us
    # Export a strictly allowlisted module audit: the raw trace stays on XPS.
    module_records = []
    for event in events:
        if event.get("event") != "module.review.completed":
            continue
        data = event.get("data")
        if not isinstance(data, dict):
            continue
        assessment = data.get("assessment")
        if not isinstance(assessment, dict):
            continue
        def safe_text(value, limit):
            if not isinstance(value, str):
                return ""
            if len(value) > limit or re.search(r"(?i)(?:bearer\\s+|github_pat_|gh[pousr]_|(?:https?://)|[a-z]:\\\\|\\\\\\\\|/home/|/users/)", value):
                return "[REDACTED_UNSAFE_TEXT]"
            return value
        module_records.append({
            "item_id": safe_text(data.get("item_id"), 128),
            "index": data.get("index") if type(data.get("index")) is int else None,
            "source_sha256": safe_text(data.get("source_sha256"), 64),
            "status": safe_text(data.get("status"), 32),
            "duration_ms": data.get("duration_ms") if type(data.get("duration_ms")) is int else None,
            "assessment": {
                "status": safe_text(assessment.get("status"), 32),
                "summary": safe_text(assessment.get("summary"), 2000),
                "uncertainty": safe_text(assessment.get("uncertainty"), 1000),
                "supporting_evidence_count": len(assessment.get("supporting_evidence", [])) if isinstance(assessment.get("supporting_evidence"), list) else None,
                "conflicting_evidence_count": len(assessment.get("conflicting_evidence", [])) if isinstance(assessment.get("conflicting_evidence"), list) else None,
            },
        })
    # Cryptographic provenance without publishing raw prompt/context or response bodies.
    request_fingerprints = {}
    response_fingerprints = {}
    for event in events:
        data = event.get("data")
        if not isinstance(data, dict):
            continue
        item_id = data.get("item_id")
        if not isinstance(item_id,str) or not SAFE_KEY.fullmatch(item_id.replace(".","_").replace("-","_")):
            continue
        if event.get("event") == "qwen.module.request" and isinstance(data.get("body"),dict):
            raw = json.dumps(data["body"],sort_keys=True,ensure_ascii=False,separators=(",",":")).encode("utf-8")
            request_fingerprints[item_id] = hashlib.sha256(raw).hexdigest()
        if event.get("event") == "qwen.module.response" and isinstance(data.get("raw"),str):
            raw = data["raw"].encode("utf-8")
            response_fingerprints[item_id] = hashlib.sha256(raw).hexdigest()
    for record in module_records:
        item_id=record["item_id"]
        record["qwen_request_sha256"] = request_fingerprints.get(item_id)
        record["qwen_response_sha256"] = response_fingerprints.get(item_id)
    if module_records and (len(module_records) != 12 or any(
        record["status"] not in ("completed", "abstain") for record in module_records
    )):
        raise ValueError("profile_report_incomplete_module_audit")
    return {
        "schema": "ezstudio.profile-execution-report.v1",
        "run_id": trace.run_id,
        "revision_id": outcome.get("revision") if isinstance(outcome, dict) and isinstance(outcome.get("revision"), int) else None,
        "status": "completed" if isinstance(outcome, dict) else "error",
        "trace_id": trace.trace_id[:12],
        "evidence_counts": counts,
        "qwen_root_keys": root_keys[:25],
        "qwen_dimension_keys": dimension_keys[:25],
        "dimensions": dimensions,
        "durations_us": durations,
        "advisory_only": True,
        "module_audit": {"count": len(module_records), "records": module_records, "raw_xps_requests_archived": False},
    }


def _gh(endpoint, *, payload=None):
    args = ["gh", "api"]
    if payload is not None:
        args += ["--method", "PUT"]
    args += [endpoint]
    if payload is not None:
        args += ["--input", "-"]
    result = subprocess.run(
        args, input=json.dumps(payload).encode("utf-8") if payload is not None else None,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=40, check=False,
    )
    if result.returncode:
        raise RuntimeError("report_github_http_error")
    return json.loads(result.stdout)


def publish_report(report):
    if os.getenv("EZS_PROFILE_REPORTS_PUBLISH", "1").strip().lower() in ("0", "false", "off"):
        return "disabled"
    run = report["run_id"]
    trace_id = report["trace_id"]
    if not isinstance(run, int) or run <= 0 or not re.fullmatch("[0-9a-f]{12}", trace_id):
        raise ValueError("report_identity_invalid")
    path = f"diagnostics/profile/run-{run:06d}/trace-{trace_id}.json"
    raw = (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    if len(raw) > 180000:
        raise ValueError("report_size_exceeded")
    endpoint = f"repos/{DEST}/contents/{path}"
    try:
        previous = _gh(endpoint)
    except RuntimeError:
        previous = None
    if previous and base64.b64decode(previous.get("content", "")) == raw:
        return "unchanged"
    payload = {
        "message": f"report: profile run {run} sanitized execution {trace_id}",
        "branch": "main",
        "content": base64.b64encode(raw).decode("ascii"),
    }
    if previous:
        payload["sha"] = previous["sha"]
    _gh(endpoint, payload=payload)
    verified = _gh(endpoint)
    if base64.b64decode(verified.get("content", "")) != raw:
        raise RuntimeError("profile_report_github_roundtrip_mismatch")
    return "published"


def publish_trace(trace, outcome):
    return publish_report(make_report(trace, outcome))
