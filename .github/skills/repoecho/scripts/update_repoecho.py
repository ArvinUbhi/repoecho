#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Download the public RepoEcho ZIP and replace the personal skill."""
import argparse
import os
import ssl
from urllib.parse import urlsplit
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


def update(zip_path=None, url=URL, home=None, ca_cert=None):
    with tempfile.TemporaryDirectory(prefix="repoecho-update-") as temp:
        temp = Path(temp)
        archive = temp / "repoecho.zip"
        if zip_path:
            shutil.copyfile(zip_path, archive)
        else:
            proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
            if proxy:
                parsed_proxy = urlsplit(proxy)
                if not parsed_proxy.hostname:
                    raise ValueError("HTTPS_PROXY is not a valid proxy URL")
                print("Using HTTPS_PROXY from this shell for the download (credentials hidden).", flush=True)
            print("Downloading RepoEcho ZIP from " + url, flush=True)
            # urllib reads HTTPS_PROXY itself and sends proxy URL credentials for CONNECT.
            # Retain TLS verification; a corporate interception certificate needs a CA file.
            context = ssl.create_default_context(cafile=str(ca_cert) if ca_cert else None)
            with urllib.request.urlopen(url, timeout=60, context=context) as response, archive.open("wb") as output:
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
    parser.add_argument("--ca-cert", type=Path, help="Corporate TLS CA PEM certificate for HTTPS proxy interception")
    args = parser.parse_args(argv)
    try:
        update(args.zip, args.url, args.home, args.ca_cert)
    except (OSError, ValueError, zipfile.BadZipFile, urllib.error.URLError, subprocess.CalledProcessError) as exc:
        # Proxy URLs can contain credentials. Never echo a raw network exception that
        # might include an environment URL or authentication header.
        if isinstance(exc, ssl.SSLCertVerificationError) or "CERTIFICATE_VERIFY_FAILED" in str(exc):
            reason = "TLS certificate verification failed. Supply your corporate CA PEM with --ca-cert PATH, or use --zip with a browser download."
        elif isinstance(exc, urllib.error.URLError):
            reason = "HTTPS download failed through this shell's proxy. Check HTTPS_PROXY and your corporate CA, or use --zip with a browser download."
        else:
            reason = str(exc)
        for value in (os.environ.get("HTTPS_PROXY"), os.environ.get("https_proxy")):
            if value:
                reason = reason.replace(value, "[proxy credentials hidden]")
        parser.exit(1, "Update failed: " + reason + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
