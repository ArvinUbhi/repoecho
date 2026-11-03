#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Copy the complete RepoEcho skill for Copilot CLI; no downloads or dependencies."""
import argparse
from pathlib import Path
import shutil
import sys
import shlex
import subprocess
import json
import os
import tempfile


def alias_expansion(destination):
    # gh shell aliases use sh on every OS; forward argv without interpolation.
    script = (destination / "scripts/repoecho_cli.py").resolve().as_posix()
    return "uv run --no-project --no-config --python '>=3.10' --script " + shlex.quote(script) + ' "$@"'


def prepare_alias(destination, replace=False):
    for executable in ("gh", "uv", "sh"):
        if not shutil.which(executable):
            raise RuntimeError(f"{executable} is required for --gh. Install it and retry; on Windows install Git for Windows for sh.")
    expansion = alias_expansion(destination)
    result = subprocess.run(["gh", "alias", "list"], capture_output=True, text=True, check=True, timeout=30)
    existing = None
    for line in result.stdout.splitlines():
        parts = line.strip().split(None, 1)
        if parts and parts[0].rstrip(":") == "repoecho":
            existing = parts[1].strip() if len(parts) > 1 else ""
            # gh alias list emits YAML scalars, not raw shell expressions.
            if existing.startswith("'") and existing.endswith("'"):
                existing = existing[1:-1].replace("''", "'")
            elif existing.startswith('"'):
                try:
                    existing = json.loads(existing)
                except ValueError:
                    pass  # Unknown encoding is a conflict, never an automatic overwrite.
    if existing is not None and existing.lstrip("!") == expansion:
        return None
    if existing is not None and not replace:
        raise RuntimeError("A different gh repoecho alias exists. Review gh alias list; use --replace-alias to replace it explicitly.")
    command = ["gh", "alias", "set", "repoecho", "--shell", "-"]
    if existing is not None:
        command.append("--clobber")
    return command, expansion


def register_alias(prepared):
    if prepared is not None:
        command, expansion = prepared
        subprocess.run(command, input=expansion, text=True, capture_output=True, check=True, timeout=30)


def command_text(destination):
    script = destination / "scripts/repoecho_cli.py"
    if os.name == "nt":
        return '@echo off\r\nREM RepoEcho CLI launcher\r\nuv run --no-project --no-config --python 3.12 --script "' + str(script) + '" %*\r\n'
    return '#!/bin/sh\n# RepoEcho CLI launcher\nexec uv run --no-project --no-config --python 3.12 --script ' + shlex.quote(str(script)) + ' "$@"\n'


def command_path(home):
    return home / ".local/bin" / ("repoecho.cmd" if os.name == "nt" else "repoecho")


def add_to_path(directory):
    """Persist a user-level PATH change; a new terminal inherits it."""
    value = str(directory)
    if os.name == "nt":
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
            try:
                current, kind = winreg.QueryValueEx(key, "Path")
            except FileNotFoundError:
                current, kind = "", winreg.REG_EXPAND_SZ
            if value.lower() not in {os.path.normcase(x.strip().strip('"')).lower() for x in current.split(";")}:
                winreg.SetValueEx(key, "Path", 0, kind if kind in (winreg.REG_SZ, winreg.REG_EXPAND_SZ) else winreg.REG_EXPAND_SZ,
                                  current.rstrip(";") + (";" if current else "") + value)
        return
    if directory in [Path(x).expanduser() for x in os.environ.get("PATH", "").split(os.pathsep) if x]:
        return
    shell = Path(os.environ.get("SHELL", "")).name
    profile = Path.home() / (".zshrc" if shell == "zsh" else ".bashrc" if shell == "bash" else ".profile")
    line = '\nexport PATH="$HOME/.local/bin:$PATH" # RepoEcho CLI\n'
    if "# RepoEcho CLI" not in (profile.read_text(encoding="utf-8") if profile.exists() else ""):
        with profile.open("a", encoding="utf-8") as output:
            output.write(line)


def write_command(destination, home, persist_path):
    target = command_path(home)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink() or (target.exists() and "RepoEcho CLI launcher" not in target.read_text(encoding="utf-8")):
        raise RuntimeError("An unrelated repoecho command already exists at " + str(target) + "; no command was replaced.")
    staged = target.with_name(target.name + ".tmp")
    staged.write_text(command_text(destination), encoding="utf-8")
    if os.name != "nt":
        staged.chmod(0o755)
    try:
        if persist_path:
            add_to_path(target.parent)
        staged.replace(target)
    finally:
        staged.unlink(missing_ok=True)
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--project", type=Path, help="Install in this repository's .github/skills")
    target.add_argument("--home", type=Path, help="Override user home (e.g. for a portable setup)")
    parser.add_argument("--no-path", action="store_true", help="Install the skill without a user PATH command")
    parser.add_argument("--replace", action="store_true", help="Replace an existing RepoEcho installation")
    parser.add_argument("--gh", action="store_true", help="Set up gh repoecho using uv (personal installation only)")
    parser.add_argument("--replace-alias", action="store_true", help="Explicitly replace a conflicting gh repoecho alias")
    args = parser.parse_args(argv)
    if args.project and args.no_path:
        parser.error("--no-path applies to personal installs only; project installs do not change PATH.")
    if args.project and args.gh:
        parser.error("Use --gh with a personal installation, then control any repository from its working directory.")
    if args.replace_alias and not args.gh:
        parser.error("--replace-alias requires --gh")
    source = Path(__file__).resolve().parents[1]
    personal_home = (args.home or Path.home()).expanduser().resolve()
    base = args.project.expanduser().resolve() / ".github/skills" if args.project else personal_home / ".copilot/skills"
    dest = base / "repoecho"
    try:
        prepared = prepare_alias(dest, args.replace_alias) if args.gh else None
    except (RuntimeError, OSError, subprocess.SubprocessError) as exc:
        parser.error(str(exc))
    if source == dest.resolve():
        register_alias(prepared)
        command = write_command(dest, personal_home, not args.home and not args.no_path) if not args.project and not args.no_path else None
        print("RepoEcho is already installed at " + str(dest))
        if command:
            print("Command: " + str(command) + " (open a new terminal for repoecho status)")
        if args.gh:
            print("Ready: gh repoecho status")
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
    with tempfile.TemporaryDirectory(prefix=".repoecho-install-", dir=base) as temp:
        staged = Path(temp) / "repoecho"
        shutil.copytree(source, staged, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        backup = Path(temp) / "previous"
        if dest.exists():
            dest.rename(backup)
        try:
            staged.rename(dest)
            register_alias(prepared)
            command = write_command(dest, personal_home, not args.home) if not args.project and not args.no_path else None
        except (RuntimeError, OSError, subprocess.SubprocessError) as exc:
            if dest.exists():
                shutil.rmtree(dest)
            if backup.exists():
                backup.rename(dest)
            parser.error("Installation rolled back: " + str(exc))
    print("Installed RepoEcho at " + str(dest))
    if command:
        print("Command: repoecho status | cache off | branch only | benchmark")
        print("Open a new terminal to pick up PATH changes; command at " + str(command))
    print("In Copilot CLI: /skills reload, then /skills info repoecho")
    print("Try: Use /repoecho to learn this repository and explain its build and main modules.")
    if args.gh:
        print("Ready: gh repoecho status | on | off | cache off | branch only | benchmark")
    return 0


if __name__ == "__main__":
    sys.exit(main())
