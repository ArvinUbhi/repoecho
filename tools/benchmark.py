#!/usr/bin/env python3
"""Reproducible end-to-end helper benchmarks; no LLM or token-savings claims."""
import argparse
import importlib.util
import json
import math
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import tempfile
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--files", type=int, default=2000)
    parser.add_argument("--notes", type=int, default=20)
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--plain", action="store_true", help="Use a non-Git source tree")
    parser.add_argument("--helper", type=Path, default=Path(__file__).resolve().parents[1] / ".github/skills/repoecho/scripts/repoecho.py")
    args = parser.parse_args()
    if min(args.files, args.notes, args.runs) < 1:
        parser.error("--files, --notes and --runs must be positive")
    spec = importlib.util.spec_from_file_location("repoecho", args.helper)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory(prefix="repoecho-benchmark-") as temp:
        root = Path(temp)
        for i in range(args.files):
            path = root / ("module%02d" % (i % 20)) / "src/main/java/example" / ("Service%d.java" % i)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("package example;\npublic class Service%d {\n" % i + "    // Representative source padding.\n" * 100 + "}\n", encoding="utf-8")
        use_git = not args.plain and shutil.which("git") is not None
        if use_git:
            for command in (["init", "-b", "main"], ["config", "user.name", "RepoEcho Benchmark"],
                            ["config", "user.email", "benchmark@example.invalid"], ["add", "."],
                            ["commit", "-m", "Synthetic benchmark fixture"]):
                subprocess.run(["git", "-C", str(root), *command], capture_output=True, check=True)

        def cli(*command):
            start = time.perf_counter()
            result = subprocess.run([sys.executable, str(args.helper), "--root", str(root), *command],
                                    capture_output=True, text=True, check=True)
            return json.loads(result.stdout), (time.perf_counter() - start) * 1000

        cold, cold_ms = cli("scan")
        start = time.perf_counter()
        m = module.Memory(root)
        try:
            m.scan()
            paths = sorted(m.manifest)
            for i in range(args.notes):
                evidence = [paths[(i * 3 + j) % len(paths)] for j in range(min(3, len(paths)))]
                receipt = m.capture(evidence, [], 24000)["receipt"]
                m.remember({"id": "service-%04d" % i, "title": "Service group %d" % i,
                            "summary": "Synthetic knowledge note for focused retrieval; not an LLM analysis.",
                            "tags": ["topic%04d" % i]}, receipt)
        finally:
            m.close()
        learning_ms = (time.perf_counter() - start) * 1000

        def samples(command, bypass=False):
            elapsed = []
            last = None
            for _ in range(args.runs):
                last, ms = cli(*command)
                elapsed.append(ms)
                assert (last.get("state") == "bypassed") == bypass
                if not bypass:
                    assert len(last["hits"]) == 1
            return {"median_ms": round(statistics.median(elapsed), 2),
                    "p95_ms": round(sorted(elapsed)[max(0, math.ceil(len(elapsed) * 0.95) - 1)], 2)}, last

        warm, last = samples(("query", "topic0000"))
        cli("mode", "off")
        mode_off, _ = samples(("query", "topic0000"), bypass=True)
        cli("mode", "on")
        cli("cache", "off")
        cache_off, _ = samples(("query", "topic0000"), bypass=True)
        cli("cache", "on")
        branch_off = None
        if use_git:
            cli("branch", "off")
            branch_off, _ = samples(("query", "topic0000"), bypass=True)
            cli("branch", "inherit")
        changed_path = root / paths[0]
        changed_path.write_text(changed_path.read_text(encoding="utf-8") + "// changed\n", encoding="utf-8")
        invalidated, changed_ms = cli("query", "topic0000")
        assert not invalidated["hits"] and invalidated["stale"]
        print(json.dumps({"files": args.files, "notes": args.notes, "runs": args.runs,
                          "repository": "git" if use_git else "plain",
                          "cold_scan_cli_ms": round(cold_ms, 2), "synthetic_learning_setup_ms": round(learning_ms, 2),
                          "warm_query_cli": warm, "mode_off_cli": mode_off,
                          "cache_off_cli": cache_off, "branch_off_cli": branch_off,
                          "changed_source_query_cli_ms": round(changed_ms, 2),
                          "stale_versions_rejected": len(invalidated["stale"]),
                          "warm_manifest_files_rehashed": last["scan"]["hashed"],
                          "warm_evidence_files_verified": last["source_files_verified"],
                          "note_chars_returned": last["content_chars"],
                          "scope": "Synthetic UTF-8 Java files. CLI timings include interpreter startup and Git work. Learning setup excludes LLM synthesis. p95 is a sample percentile, not an SLA."}, indent=2))


if __name__ == "__main__":
    main()
