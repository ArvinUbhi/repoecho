#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Download the public RepoEcho ZIP and replace the personal skill."""
import argparse
import hashlib
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
MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
MAX_EXPANDED_BYTES = 256 * 1024 * 1024
MAX_ARCHIVE_FILES = 10000
VERSION_PATTERN = re.compile(r'^VERSION = "(\d+)\.(\d+)\.(\d+)"$', re.M)


def version(path):
    match = VERSION_PATTERN.search(path.read_text(encoding="utf-8"))
    if not match:
        raise ValueError("RepoEcho ZIP has no valid MAJOR.MINOR.PATCH version")
    return tuple(map(int, match.groups()))


def update(zip_path=None, url=URL, home=None, ca_cert=None, sha256=None):
    if sha256 is not None and not re.fullmatch(r"[0-9a-fA-F]{64}", sha256):
        raise ValueError("--sha256 must contain exactly 64 hexadecimal characters")
    parsed_url = urlsplit(url)
    if not zip_path and (parsed_url.scheme != "https" or not parsed_url.hostname or
                         parsed_url.username is not None or parsed_url.password is not None):
        raise ValueError("Update URL must use HTTPS without embedded credentials")
    with tempfile.TemporaryDirectory(prefix="repoecho-update-") as temp:
        temp = Path(temp)
        archive = temp / "repoecho.zip"
        if zip_path:
            if Path(zip_path).stat().st_size > MAX_ARCHIVE_BYTES:
                raise ValueError("Update ZIP exceeds the 64 MiB limit")
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
                total = 0
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_ARCHIVE_BYTES:
                        raise ValueError("Update ZIP exceeds the 64 MiB limit")
                    output.write(chunk)
        if sha256 is not None:
            actual = hashlib.sha256(archive.read_bytes()).hexdigest()
            if actual != sha256.lower():
                raise ValueError("Update ZIP SHA-256 does not match the approved checksum; nothing installed")
        with zipfile.ZipFile(archive) as bundle:
            entries = bundle.infolist()
            if len(entries) > MAX_ARCHIVE_FILES or sum(x.file_size for x in entries) > MAX_EXPANDED_BYTES:
                raise ValueError("Update ZIP exceeds file count or expanded size limits")
            names = bundle.namelist()
            roots = {p.split("/", 1)[0] for p in names if "/" in p}
            if len(roots) != 1 or any(".." in Path(n).parts or n.startswith("/") or ":" in n or "\\" in n for n in names):
                raise ValueError("Unexpected or unsafe ZIP paths")
            root_name = roots.pop()
            prefix = root_name + "/"
            if len(names) != len(set(names)) or any(not n.startswith(prefix) for n in names):
                raise ValueError("Unexpected or duplicate ZIP entries")
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
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--url", help="HTTPS ZIP URL; default is the public main branch")
    source.add_argument("--ref", help="Approved full Git commit SHA for a pinned team update")
    parser.add_argument("--sha256", help="Expected ZIP checksum supplied by your team; checked before installation")
    parser.add_argument("--home", type=Path, help="Portable/test installation home; do not alter current user PATH")
    parser.add_argument("--ca-cert", type=Path, help="Corporate TLS CA PEM certificate for HTTPS proxy interception")
    args = parser.parse_args(argv)
    try:
        if args.ref and not re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", args.ref):
            raise ValueError("--ref requires a full Git commit SHA")
        if args.zip and (args.ref or args.url):
            raise ValueError("Use --zip alone or select a download with --ref/--url")
        url = ("https://github.com/ArvinUbhi/repoecho/archive/" + args.ref + ".zip") if args.ref else (args.url or URL)
        update(args.zip, url, args.home, args.ca_cert, args.sha256)
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
