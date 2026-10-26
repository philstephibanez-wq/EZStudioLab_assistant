#!/usr/bin/env python3
"""Read-only benchmark of two explicitly supplied OpenAI-compatible endpoints."""
import argparse
import json
import statistics
import time
import urllib.error
import urllib.request
from pathlib import Path

PROMPTS = [
    "Réponds seulement en JSON avec les clés verdict et raison. Sans source indépendante concernant un enregistrement musical, quel verdict donner ?",
    "Une source décrit une reprise et non l'enregistrement original. Peut-elle prouver sa tonalité ? Réponds en une phrase en français.",
    "Réponds en JSON valide avec les clés bon, faux et non_trouve, chacune avec une explication de cinq mots maximum.",
]


def post(base, payload, timeout):
    req = urllib.request.Request(
        base.rstrip("/") + "/v1/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as result:
        return json.load(result)


def measure(base, model, prompt, timeout):
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 120,
        "stream": False,
    }
    start = time.perf_counter()
    result = post(base, payload, timeout)
    wall_ms = round(1000 * (time.perf_counter() - start), 2)
    text = result["choices"][0]["message"]["content"]
    timings = result.get("timings") or {}
    usage = result.get("usage") or {}
    tokens = usage.get("completion_tokens") or timings.get("predicted_n")
    return {
        "wall_ms": wall_ms,
        "completion_tokens": tokens,
        "wall_tokens_per_s": round(tokens * 1000 / wall_ms, 2) if tokens and wall_ms else None,
        "server_predicted_tokens_per_s": timings.get("predicted_per_second"),
        "server_prompt_ms": timings.get("prompt_ms"),
        "output": text,
        "json_valid": _valid_json(text),
    }


def _valid_json(value):
    try:
        return isinstance(json.loads(value), dict)
    except (ValueError, TypeError):
        return False


def run(endpoints, model, timeout, repeats):
    # Sequential calls: never create GPU contention between endpoints.
    output = {"model": model, "config": {"temperature": 0, "max_tokens": 120, "repeats": repeats}, "runs": {}}
    for name, url in endpoints:
        rows = []
        for prompt_index, prompt in enumerate(PROMPTS):
            for sample in range(repeats):
                result = measure(url, model, prompt, timeout)
                rows.append({"prompt_index": prompt_index, "sample": sample, **result})
        speeds = [row["wall_tokens_per_s"] for row in rows if row["wall_tokens_per_s"] is not None]
        output["runs"][name] = {
            "endpoint": url,
            "results": rows,
            "median_wall_tokens_per_s": statistics.median(speeds) if speeds else None,
            "json_valid_count": sum(row["json_valid"] for row in rows),
        }
    return output


def main():
    p = argparse.ArgumentParser(description="Benchmark séquentiel : mêmes requêtes vers deux moteurs compatibles OpenAI")
    p.add_argument("--cuda-url", required=True)
    p.add_argument("--vulkan-url", required=True)
    p.add_argument("--model", required=True, help="Même GGUF sur les deux serveurs")
    p.add_argument("--timeout", type=int, default=120)
    p.add_argument("--repeats", type=int, default=2)
    p.add_argument("--output", required=True, help="Fichier JSON sous H:\\temp (hors Git)")
    args = p.parse_args()
    if args.repeats < 1 or args.repeats > 5:
        p.error("--repeats doit être entre 1 et 5")
    if args.cuda_url.rstrip("/") == args.vulkan_url.rstrip("/"):
        p.error("Les deux URLs doivent être différentes")
    dest = Path(args.output)
    if not str(dest).lower().startswith("h:\\temp\\"):
        p.error("Le rapport doit être enregistré sous H:\\temp")
    try:
        result = run([("cuda", args.cuda_url), ("vulkan", args.vulkan_url)], args.model, args.timeout, args.repeats)
    except (urllib.error.URLError, TimeoutError, KeyError, ValueError) as exc:
        p.exit(2, "BENCHMARK_INCOMPLETE: " + str(exc) + "\n")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name, entry in result["runs"].items():
        print(f"{name}: median_wall_tokens_per_s={entry['median_wall_tokens_per_s']} json_valid={entry['json_valid_count']}/{len(entry['results'])}")
    print("RESULT_JSON=" + str(dest))


if __name__ == "__main__":
    main()
