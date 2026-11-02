#!/usr/bin/env python3
"""Synthetic cache benchmark, not an LLM latency/token-savings benchmark."""
import argparse
import importlib.util
import json
from pathlib import Path
import statistics
import tempfile
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--files", type=int, default=2000)
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--helper", type=Path, default=Path(__file__).resolve().parents[1] / ".github/skills/repoecho/scripts/repoecho.py")
    args = parser.parse_args()
    if args.files < 1 or args.runs < 1:
        parser.error("--files and --runs must be positive")
    spec = importlib.util.spec_from_file_location("repoecho", args.helper)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory(prefix="repoecho-benchmark-") as temp:
        root = Path(temp)
        for i in range(args.files):
            path = root / ("module%02d" % (i % 20)) / "src/main/java/example" / ("Service%d.java" % i)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("package example;\npublic class Service%d {\n" % i + "    // Representative source padding.\n" * 100 + "}\n", encoding="utf-8")
        m = module.Memory(root)
        try:
            cold = m.scan()
            paths = sorted(m.manifest)[:3]
            receipt = m.capture(paths, [], 24000)["receipt"]
            m.remember({"id": "sample", "title": "Service lookup", "summary": "Synthetic benchmark note about service classes.", "tags": ["service"]}, receipt)
            warm, queries = [], []
            for _ in range(args.runs):
                warm.append(m.scan()["elapsed_ms"])
                start = time.perf_counter()
                result = m.query("service")
                queries.append((time.perf_counter() - start) * 1000)
                assert len(result["hits"]) == 1
            print(json.dumps({"files": args.files, "runs": args.runs, "cold_scan_ms": cold["elapsed_ms"],
                              "warm_scan_median_ms": round(statistics.median(warm), 2),
                              "query_median_ms": round(statistics.median(queries), 2),
                              "query_source_files_verified": result["source_files_verified"],
                              "warm_files_rehashed": result["scan"]["hashed"],
                              "note_chars_returned": result["content_chars"],
                              "scope": "Synthetic UTF-8 Java tree, one note, three evidence files; excludes process startup and LLM work."}, indent=2))
        finally:
            m.close()


if __name__ == "__main__":
    main()
