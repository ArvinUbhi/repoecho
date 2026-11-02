#!/usr/bin/env python3
"""Copy the complete RepoEcho skill for Copilot CLI; no downloads or dependencies."""
import argparse
from pathlib import Path
import shutil
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--project", type=Path, help="Install in this repository's .github/skills")
    target.add_argument("--home", type=Path, help="Override user home (e.g. for a portable setup)")
    parser.add_argument("--replace", action="store_true", help="Replace an existing RepoEcho installation")
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[1] / ".github/skills/repoecho"
    base = args.project.expanduser().resolve() / ".github/skills" if args.project else (args.home or Path.home()).expanduser().resolve() / ".copilot/skills"
    dest = base / "repoecho"
    if source == dest.resolve():
        print("RepoEcho is already installed at " + str(dest))
        return 0
    if dest.is_symlink():
        parser.error("Refusing to replace a symlink. Choose a normal skill directory.")
    if dest.exists():
        if not args.replace:
            parser.error("Destination exists; review it and rerun with --replace to update.")
        if not (dest / "SKILL.md").is_file():
            parser.error("Existing destination is not a skill directory; no files changed.")
    base.mkdir(parents=True, exist_ok=True)
    # Stage completely before replacing a previous installation; roll back on failure.
    import tempfile
    with tempfile.TemporaryDirectory(prefix=".repoecho-install-", dir=base) as temp:
        staged = Path(temp) / "repoecho"
        shutil.copytree(source, staged, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        backup = Path(temp) / "previous"
        if dest.exists():
            dest.rename(backup)
        try:
            staged.rename(dest)
        except OSError:
            if backup.exists():
                backup.rename(dest)
            raise
    print("Installed RepoEcho at " + str(dest))
    print("In Copilot CLI: /skills reload, then /skills info repoecho")
    print("Try: Use /repoecho to learn this repository and explain its build and main modules.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
