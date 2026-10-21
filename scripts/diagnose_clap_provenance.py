"""Read-only SHA-256 provenance investigation for PROFILE CLAP archives.

Does not perform inference, mutate presets, or treat a reconstructed
source as an integrity pass. Only paths and hashes are reported.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

MODULE = "semantic.clap-open-vocabulary"


def read_json(path):
    raw = Path(path).read_bytes()
    encoding = "utf-16" if raw.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig"
    return json.loads(raw.decode(encoding))


def digest(value):
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def get_module(value):
    if not isinstance(value, dict):
        raise ValueError("invalid_source_object")
    if value.get("id") == MODULE:
        return value
    if "fields" in value:
        modules = value["fields"]["diagnostics_json"]["module_registry"]["modules"]
    elif isinstance(value.get("modules"), list):
        modules = value["modules"]
    else:
        raise ValueError("module_collection_missing")
    found = [m for m in modules if isinstance(m, dict) and m.get("id") == MODULE]
    if len(found) != 1:
        raise ValueError("clap_module_count_invalid")
    return found[0]


def changed_paths(archived, reference, root="$"):
    """List changed JSON paths, never values (including private model paths)."""
    if type(archived) is not type(reference):
        return [{"path": root, "kind": "type_changed"}]
    if isinstance(archived, dict):
        out = []
        for key in sorted(archived.keys() | reference.keys()):
            next_path = root + "." + str(key)
            if key not in archived:
                out.append({"path": next_path, "kind": "only_in_reference"})
            elif key not in reference:
                out.append({"path": next_path, "kind": "only_in_archive"})
            else:
                out.extend(changed_paths(archived[key], reference[key], next_path))
        return out
    if isinstance(archived, list):
        out = []
        for index in range(max(len(archived), len(reference))):
            next_path = root + "[" + str(index) + "]"
            if index >= len(archived):
                out.append({"path": next_path, "kind": "only_in_reference"})
            elif index >= len(reference):
                out.append({"path": next_path, "kind": "only_in_archive"})
            else:
                out.extend(changed_paths(archived[index], reference[index], next_path))
        return out
    return [] if archived == reference else [{"path": root, "kind": "value_changed"}]


def diagnose(lab, revision, reference=None):
    archived = get_module(lab)
    records = revision["fields"]["comparison_json"]["module_consultations"]["results"]
    matches = [r for r in records if r.get("item_id") == MODULE]
    if len(matches) != 1:
        raise ValueError("clap_consultation_count_invalid")
    expected = matches[0]["source_sha256"]
    actual = digest(archived)
    result = {
        "schema": "ezstudio.clap-forensic.r1",
        "module": MODULE,
        "archived_sha256": actual,
        "qwen_source_sha256": expected,
        "match": actual == expected,
        "status": "matched" if actual == expected else "unexplained_mismatch",
        "reference_supplied": reference is not None,
        "reference_matches_qwen_sha256": None,
        "source_mutation_proven": False,
        "difference_paths": [],
        "integrity_complete": actual == expected,
        "no_inference_performed": True,
        "no_science_change": True,
    }
    if reference is not None:
        original = get_module(reference)
        reference_hash = digest(original)
        result["reference_sha256"] = reference_hash
        result["reference_matches_qwen_sha256"] = reference_hash == expected
        result["difference_paths"] = changed_paths(archived, original)
        result["source_mutation_proven"] = bool(reference_hash == expected and result["difference_paths"])
        if result["source_mutation_proven"]:
            result["status"] = "reference_matches_qwen_and_diff_identified"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lab", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--reference", help="Optional original full source module or LAB archive")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = diagnose(read_json(args.lab), read_json(args.revision),
                      read_json(args.reference) if args.reference else None)
    dest = Path(args.output)
    if dest.exists():
        raise FileExistsError("output_exists")
    if not dest.parent.is_dir():
        raise FileNotFoundError("output_parent_missing")
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("CLAP_FORENSIC", result["status"], "integrity_complete", result["integrity_complete"],
          "difference_paths", len(result["difference_paths"]))
    if not result["integrity_complete"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
