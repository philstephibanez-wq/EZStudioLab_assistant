"""Fetch the exact published PROFILE archive with binary-safe GitHub CLI transport.

The input to the SHA contract is the parsed JSON document. Avoid piping
native UTF-8 output through Windows PowerShell 5.1 text decoding.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path


REPOSITORY = "repos/philstephibanez-wq/EZStudio_Run_Reports/contents"


def digest(value):
    data = json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def validate_archive(raw, run_id):
    doc = json.loads(raw.decode("utf-8-sig"))
    if (not isinstance(doc, dict) or doc.get("schema") != "ezstudio.diagnostics.main.v1"
            or doc.get("producer") != "lab" or doc.get("phase") != "profile"
            or doc.get("run_id") != run_id
            or doc.get("fields", {}).get("id") != run_id):
        raise ValueError("unexpected_lab_archive_identity")
    registry = doc["fields"]["diagnostics_json"]["module_registry"]["modules"]
    attestations = doc.get("module_integrity")
    if not isinstance(registry, list) or not isinstance(attestations, list) or len(registry) != len(attestations):
        raise ValueError("module_integrity_coverage_invalid")
    by_id = {}
    for row in attestations:
        if not isinstance(row, dict) or not isinstance(row.get("module"), str) or row["module"] in by_id:
            raise ValueError("module_attestation_identity_invalid")
        by_id[row["module"]] = row
    if len(by_id) != len(registry):
        raise ValueError("module_attestation_coverage_invalid")
    seen = set()
    for item in registry:
        key = item["id"]
        if key in seen or key not in by_id:
            raise ValueError("module_attestation_identity_invalid")
        seen.add(key)
        row = by_id[key]
        observed = digest(item)
        if observed != row.get("archive_sha256_after_redaction"):
            raise ValueError("archive_sha_mismatch:" + key)
        pre = row.get("source_sha256_before_redaction")
        if (not isinstance(pre, str) or len(pre) != 64
                or row.get("archive_changed") is not (pre != observed)):
            raise ValueError("archive_attestation_inconsistent:" + key)
    return len(registry)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run-id", type=int, default=153)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    if args.run_id < 1:
        p.error("run-id must be positive")
    endpoint = f"{REPOSITORY}/diagnostics/lab/profile/run-{args.run_id:06d}/main-db.json"
    proc = subprocess.run(["gh", "api", endpoint, "-H",
                           "Accept: application/vnd.github.raw+json"],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if proc.returncode:
        raise RuntimeError("gh_api_download_failed_rc_" + str(proc.returncode))
    count = validate_archive(proc.stdout, args.run_id)
    dest = Path(args.output)
    if not dest.parent.is_dir():
        raise FileNotFoundError("output_parent_missing")
    fd, tmp = tempfile.mkstemp(prefix=".profile-archive-", suffix=".json", dir=str(dest.parent))
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(proc.stdout)
        os.replace(tmp, dest)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    print(f"PROFILE_ARCHIVE_TRANSPORT_VERIFIED run={args.run_id} modules={count} output={dest}")


if __name__ == "__main__":
    main()
