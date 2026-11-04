import json
import io
import base64
import urllib.request
import ssl
import zipfile
import os
import re
import shlex
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

PROJECT = Path(__file__).resolve().parents[1]


class InstallTests(unittest.TestCase):
    def install(self, *args):
        return subprocess.run([sys.executable, str(PROJECT / "tools/install.py"), *map(str, args)],
                              capture_output=True, text=True)

    def test_personal_install_and_replace_guard(self):
        with tempfile.TemporaryDirectory() as home:
            result = self.install("--home", home)
            self.assertEqual(result.returncode, 0, result.stderr)
            target = Path(home) / ".copilot/skills/repoecho"
            self.assertTrue((target / "SKILL.md").exists())
            self.assertTrue((target / "references/java.md").exists())
            launcher = Path(home) / ".local/bin" / ("repoecho.cmd" if os.name == "nt" else "repoecho")
            self.assertTrue(launcher.exists())
            self.assertIn("--python 3.12", launcher.read_text())
            if os.name == "nt":
                match = re.search(r'--script "([^"]+)"', launcher.read_text())
                self.assertIsNotNone(match)
                script = match.group(1)
            else:
                parts = shlex.split(launcher.read_text().splitlines()[-1])
                script = parts[parts.index("--script") + 1]
            self.assertTrue(Path(script).samefile(target / "scripts/repoecho_cli.py"))
            helper = target / "scripts/repoecho.py"
            result = subprocess.run([sys.executable, str(helper), "--root", home, "scan"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("files", json.loads(result.stdout))
            self.assertNotEqual(self.install("--home", home).returncode, 0)
            self.assertEqual(self.install("--home", home, "--replace").returncode, 0)
            self.assertEqual(launcher.read_text().count("repoecho_cli.py"), 1)

    @unittest.skipIf(os.name == "nt", "POSIX launcher integration test")
    def test_launcher_forwards_arguments_from_another_repository(self):
        with tempfile.TemporaryDirectory() as home:
            self.assertEqual(self.install("--home", home).returncode, 0)
            fake_bin = Path(home) / "fake-bin"
            fake_bin.mkdir()
            uv = fake_bin / "uv"
            uv.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n')
            uv.chmod(0o755)
            launcher = Path(home) / ".local/bin/repoecho"
            result = subprocess.run([str(launcher), "--root", str(Path(home) / "repository with spaces"), "cache", "off"],
                                    env={**os.environ, "PATH": str(fake_bin) + os.pathsep + os.environ.get("PATH", "")},
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.splitlines()[-4:], ["--root", str(Path(home) / "repository with spaces"), "cache", "off"])

    def test_no_path_keeps_personal_skill_available(self):
        with tempfile.TemporaryDirectory() as home:
            result = self.install("--home", home, "--no-path")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((Path(home) / ".local/bin").exists())
            self.assertTrue((Path(home) / ".copilot/skills/repoecho/SKILL.md").exists())

    def test_existing_unrelated_command_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as home:
            launcher = Path(home) / ".local/bin" / ("repoecho.cmd" if os.name == "nt" else "repoecho")
            launcher.parent.mkdir(parents=True)
            launcher.write_text("another tool")
            result = self.install("--home", home)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(launcher.read_text(), "another tool")
            self.assertFalse((Path(home) / ".copilot/skills/repoecho").exists())

    def test_offline_zip_updater_and_downgrade_guard(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "source.zip"
            with zipfile.ZipFile(archive, "w") as z:
                for path in PROJECT.rglob("*"):
                    if path.is_file() and not any(x in path.parts for x in (".git", "__pycache__", ".repoecho")):
                        z.write(path, "repoecho-main/" + path.relative_to(PROJECT).as_posix())
            home = root / "user"
            updater = PROJECT / ".github/skills/repoecho/scripts/update_repoecho.py"
            result = subprocess.run([sys.executable, str(updater), "--zip", str(archive), "--home", str(home)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            installed = home / ".copilot/skills/repoecho/scripts/repoecho.py"
            self.assertIn('VERSION = "1.3.3"', installed.read_text())
            installed.write_text(installed.read_text().replace('VERSION = "1.3.3"', 'VERSION = "9.0.0"'))
            result = subprocess.run([sys.executable, str(updater), "--zip", str(archive), "--home", str(home)],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('VERSION = "9.0.0"', installed.read_text())

    def test_proxy_environment_download_keeps_tls_verification(self):
        import importlib.util
        updater_path = PROJECT / ".github/skills/repoecho/scripts/update_repoecho.py"
        spec = importlib.util.spec_from_file_location("updater", updater_path)
        updater = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(updater)
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as bundle:
            bundle.writestr("repoecho-main/tools/install.py", "# placeholder")
            bundle.writestr("repoecho-main/.github/skills/repoecho/scripts/repoecho.py", 'VERSION = "1.3.3"\n')
        with tempfile.TemporaryDirectory() as home, \
             mock.patch.dict(os.environ, {"HTTPS_PROXY": "http://user:secret@proxy.example:8080"}), \
             mock.patch.object(updater.urllib.request, "urlopen", return_value=io.BytesIO(stream.getvalue())) as download, \
             mock.patch.object(updater.subprocess, "run"):
            updater.update(home=home)
            self.assertEqual(download.call_args.kwargs["context"].verify_mode, ssl.CERT_REQUIRED)
            self.assertNotIn("secret", str(download.call_args))

    def test_python_proxy_handler_uses_profile_url_credentials(self):
        proxy = "http://first:complex%40password@proxy.example:8080"
        request = urllib.request.Request("https://github.com/ArvinUbhi/repoecho/archive/refs/heads/main.zip")
        with mock.patch.object(urllib.request, "proxy_bypass", return_value=False):
            urllib.request.ProxyHandler({"https": proxy}).proxy_open(request, proxy, "https")
        header = request.get_header("Proxy-authorization")
        self.assertEqual(base64.b64decode(header.split()[1]).decode(), "first:complex@password")

    def test_project_install(self):
        with tempfile.TemporaryDirectory() as root:
            result = self.install("--project", root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((Path(root) / ".github/skills/repoecho/scripts/repoecho.py").is_file())


if __name__ == "__main__":
    unittest.main()
