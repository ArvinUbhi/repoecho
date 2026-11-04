#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Download the public RepoEcho ZIP and replace the personal skill."""
import argparse
from pathlib import Path
import re
import shutil
import sys
import subprocess
import urllib.error
import tempfile
import urllib.request
import zipfile

URL = "https://github.com/ArvinUbhi/repoecho/archive/refs/heads/main.zip"
VERSION_PATTERN = re.compile(r'^VERSION = "(\d+)\.(\d+)\.(\d+)"$', re.M)


def version(path):
    match = VERSION_PATTERN.search(path.read_text(encoding="utf-8"))
    if not match:
        raise ValueError("RepoEcho ZIP has no valid MAJOR.MINOR.PATCH version")
    return tuple(map(int, match.groups()))


def update(zip_path=None, url=URL, home=None):
    with tempfile.TemporaryDirectory(prefix="repoecho-update-") as temp:
        temp = Path(temp)
        archive = temp / "repoecho.zip"
        if zip_path:
            shutil.copyfile(zip_path, archive)
        else:
            print("Downloading RepoEcho ZIP from " + url, flush=True)
            with urllib.request.urlopen(url, timeout=60) as response, archive.open("wb") as output:
                shutil.copyfileobj(response, output)
        with zipfile.ZipFile(archive) as bundle:
            names = bundle.namelist()
            roots = {p.split("/", 1)[0] for p in names if "/" in p}
            if len(roots) != 1 or any(".." in Path(n).parts or n.startswith("/") or "\\" in n for n in names):
                raise ValueError("Unexpected or unsafe ZIP paths")
            root_name = roots.pop()
            prefix = root_name + "/"
            required = {prefix + "tools/install.py", prefix + ".github/skills/repoecho/scripts/repoecho.py"}
            if not required.issubset(names):
                raise ValueError("ZIP is not a RepoEcho source checkout")
            bundle.extractall(temp / "source")
        root = temp / "source" / root_name
        new = version(root / ".github/skills/repoecho/scripts/repoecho.py")
        home_path = Path(home).expanduser().resolve() if home else Path.home().resolve()
        installed = home_path / ".copilot/skills/repoecho/scripts/repoecho.py"
        if installed.exists():
            old = version(installed)
            if new < old:
                raise ValueError(f"Refusing to replace version {old} with older version {new}")
            print("Installed: " + ".".join(map(str, old)))
        print("Downloaded: " + ".".join(map(str, new)), flush=True)
        installer = root / "tools/install.py"
        # Use the uv-selected interpreter; the target repository's Python is untouched.
        command = [sys.executable, str(installer), "--replace"]
        if home:
            command += ["--home", str(home_path)]
        subprocess.run(command, check=True)
        print("Updated RepoEcho to " + ".".join(map(str, new)) + ". Reload skills in Copilot.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path, help="Browser-downloaded ZIP when the proxy blocks scripted downloads")
    parser.add_argument("--url", default=URL, help="ZIP URL; default is the public main branch")
    parser.add_argument("--home", type=Path, help="Portable/test installation home; do not alter current user PATH")
    args = parser.parse_args(argv)
    try:
        update(args.zip, args.url, args.home)
    except (OSError, ValueError, zipfile.BadZipFile, urllib.error.URLError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"Update failed: {exc}\nIf your proxy blocks this download, save the ZIP in your browser and run repoecho update --zip PATH\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
