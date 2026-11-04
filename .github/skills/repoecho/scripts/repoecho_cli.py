#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Friendly RepoEcho commands, backed by the same engine used by the skill."""
import argparse
import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys

import repoecho


def repository_root(explicit=None):
    if explicit is not None:
        return repoecho.root_path(explicit)
    if shutil.which("git"):
        result = repoecho.git_run(Path.cwd(), "rev-parse", "--show-toplevel")
        if result.returncode == 0:
            return repoecho.root_path(result.stdout.decode("utf-8").strip())
        if "not a git repository" not in result.stderr.decode(errors="replace").lower():
            raise repoecho.CacheError("Git could not identify the repository. Resolve the Git error or specify --root explicitly.")
    root = Path.cwd().resolve()
    if not shutil.which("git"):
        repoecho.require_plain_without_git(root)
    return root


def show_controls(state, root):
    print("RepoEcho " + ("ON" if state["effective_enabled"] else "BYPASSED"))
    print("Repository: " + str(root))
    print("Branch: " + (state["current_branch"] or state["branch_kind"]))
    print(f"Skill: {state['skill']} | Cache: {state['cache']} | Branch: {state['branch']} ({state['branch_rule']})")
    if state["bypass_reasons"]:
        print("Disabled by: " + ", ".join(state["bypass_reasons"]))
    print("Other branches default: " + state["branch_default"])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, prog="repoecho",
        epilog="Examples: repoecho off; repoecho cache on; repoecho branch only; repoecho benchmark. Put --root and --json before the command.")
    parser.add_argument("--root", help="Explicit repository/subtree; otherwise find the Git worktree root")
    parser.add_argument("--json", action="store_true", help="Machine-readable control/doctor output")
    parser.add_argument("--version", action="version", version=repoecho.VERSION)
    parser.add_argument("command", nargs="?", default="status",
        help="status, on, off, mode, cache, branch, doctor, benchmark, setup; or any engine command")
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    if args.command == "update":
        if args.root is not None or args.json:
            parser.error("update does not accept --root or --json")
        import update_repoecho
        return update_repoecho.main(args.arguments)
    if args.command in ("setup", "benchmark"):
        if args.root is not None or args.json:
            parser.error("setup/benchmark use their own options; run the command with --help")
        if args.command == "setup":
            import setup_repoecho
            return setup_repoecho.main(args.arguments)
        import benchmark
        return benchmark.main(args.arguments) or 0
    try:
        root = repository_root(args.root)
        command = args.command
        arguments = args.arguments
        if command in ("on", "off", "status", "doctor") and arguments:
            parser.error(f"{command} does not accept extra arguments; put --root/--json before the command")
        if command == "doctor":
            state = repoecho.Controls(root).report()
            result = {"version": repoecho.VERSION, "repository": str(root), "python": sys.version.split()[0],
                      "skill": str(Path(__file__).resolve().parents[1]),
                      "tools": {name: shutil.which(name) for name in ("uv", "gh", "git", "sh")}, "controls": state}
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(f"RepoEcho {result['version']} | Python {result['python']}")
                print("Skill: " + result["skill"])
                for name, path in result["tools"].items():
                    print(name + ": " + (path or "not found"))
                show_controls(state, root)
                print("No source scan or knowledge database access performed.")
            return 0
        if command in ("on", "off"):
            command, arguments = "mode", [command]
        elif command == "status":
            command = "mode"  # Fast status should not trigger a repository scan.
        elif command == "inspect":
            command = "status"  # Explicit deep status; preserves the engine API.
        if command not in ("mode", "cache", "branch") or args.json or any(x in arguments for x in ("--help", "-h")):
            return repoecho.main(["--root", str(root), command, *arguments])
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = repoecho.main(["--root", str(root), command, *arguments])
        if result == 0:
            show_controls(json.loads(output.getvalue())["controls"], root)
        return result
    except (repoecho.CacheError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
