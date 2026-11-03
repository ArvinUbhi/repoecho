#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Create and summarize manually recorded Copilot runs; stdlib only."""
import argparse
import csv
from pathlib import Path
import statistics

PROMPTS = [
    "Explain how a running job is stopped.",
    "Explain the startup workflow.",
    "Where is configuration loaded and applied?",
    "What happens when a worker fails?",
    "Which tests cover process termination?",
]
FIELDS = ["question_id", "question", "mode", "model", "branch_commit", "aic", "elapsed_seconds", "helper_calls", "correct"]
MODES = ("off", "cold", "warm")


def init(path):
    if path.exists():
        raise ValueError("File already exists; choose another filename to preserve your results")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        for i, prompt in enumerate(PROMPTS, 1):
            for mode in MODES:
                writer.writerow({"question_id": i, "question": prompt, "mode": mode})
    print(f"Created {path}. Replace example questions and record each fresh Copilot session.")


def report(path):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not set(FIELDS) <= set(reader.fieldnames or []):
            raise ValueError("Missing required columns: " + ", ".join(sorted(set(FIELDS) - set(reader.fieldnames or []))))
        rows = list(reader)
    groups = {}
    for row in rows:
        if not row["aic"].strip():
            continue
        mode = row["mode"].strip()
        if mode not in MODES or row["correct"].lower() not in {"yes", "no"}:
            raise ValueError("Completed rows need mode off/cold/warm and correct yes/no")
        aic = float(row["aic"])
        elapsed = float(row["elapsed_seconds"])
        calls = int(row["helper_calls"])
        if min(aic, elapsed, calls) < 0:
            raise ValueError("Metrics cannot be negative")
        key = (row["question_id"].strip(), row["question"].strip(), row["model"].strip(), row["branch_commit"].strip())
        if not all(key):
            raise ValueError("Completed rows need question_id, model and branch_commit")
        groups.setdefault(key, {}).setdefault(mode, []).append((aic, elapsed, calls, row["correct"].lower() == "yes"))
    for comparison in ("cold", "warm"):
        pairs = [(statistics.median(run[0] for run in x["off"]),
                  statistics.median(run[0] for run in x[comparison]))
                 for x in groups.values() if "off" in x and comparison in x]
        if not pairs:
            print(f"{comparison}: no complete matched questions yet")
            continue
        deltas = [(off - enabled) / off * 100 for off, enabled in pairs if off > 0]
        if deltas:
            print(f"{comparison} versus off: {len(pairs)} matched questions; "
                  f"median AIC reduction {statistics.median(deltas):.1f}%")
        else:
            print("No positive baseline AIC")
    for mode in MODES:
        samples = [value for group in groups.values() for value in group.get(mode, [])]
        if samples:
            print(f"{mode}: {len(samples)} runs, median AIC {statistics.median(x[0] for x in samples):.2f}, "
                  f"median seconds {statistics.median(x[1] for x in samples):.2f}, "
                  f"median helper calls {statistics.median(x[2] for x in samples):.1f}, "
                  f"correct {sum(x[3] for x in samples)}/{len(samples)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("init", "report"))
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    try:
        (init if args.action == "init" else report)(args.file)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
