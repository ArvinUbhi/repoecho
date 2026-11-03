#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Reproducible retrieval cases on disposable synthetic evidence."""
import importlib.util
import json
from pathlib import Path
import tempfile

HELPER = Path(__file__).resolve().parents[1] / ".github/skills/repoecho/scripts/repoecho.py"
spec = importlib.util.spec_from_file_location("repoecho", HELPER)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

CASES = [
    ("What happens when I stop a running job?", "process-stop"),
    ("How does process termination work?", "process-stop"),
    ("How do I shut down a host?", "host-stop"),
    ("Where is the host stopped?", "host-stop"),
    ("How is configuration refreshed?", "config-reload"),
    ("Where are invoice payments settled?", None),
]


def main():
    with tempfile.TemporaryDirectory(prefix="repoecho-retrieval-eval-") as temp:
        root = Path(temp)
        notes = [
            ("process-stop", "Stop a running process", "Process shutdown", "stop a running job", "process termination"),
            ("host-stop", "Stop a host", "Host shutdown", "shut down a host", "stop host"),
            ("config-reload", "Reload configuration", "Configuration refresh", "refresh configuration", "reload settings"),
        ]
        memory = module.Memory(root)
        for note_id, title, summary, *aliases in notes:
            path = f"src/{note_id}.java"
            (root / "src").mkdir(exist_ok=True)
            (root / path).write_text("class Example { void run() {} }\n", encoding="utf-8")
            receipt = memory.capture([path], [], 24000)["receipt"]
            memory.remember({"id": note_id, "title": title, "summary": summary,
                             "aliases": aliases, "facts": [path + ":1 defines the entry point."]}, receipt)
        outcomes = []
        for query, expected in CASES:
            actual = memory.query(query, limit=1, compact=True)["hits"]
            found = actual[0]["id"] if actual else None
            outcomes.append({"question": query, "expected": expected, "found": found,
                             "correct": found == expected})
        # Changed evidence must suppress the answer despite matching wording.
        (root / "src/process-stop.java").write_text("changed\n", encoding="utf-8")
        stale = memory.query(CASES[0][0], limit=1, compact=True)
        stale_rejected = not stale["hits"] and any(x["id"] == "process-stop" for x in stale["stale"])
        memory.close()
        result = {"correct_at_1": sum(x["correct"] for x in outcomes), "total": len(outcomes),
                  "stale_rejected": stale_rejected, "cases": outcomes,
                  "scope": "Synthetic lexical and alias cases; no Copilot model, no user repository."}
        print(json.dumps(result, indent=2))
        if result["correct_at_1"] != len(CASES) or not stale_rejected:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
