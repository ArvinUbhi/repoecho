import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

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
            self.assertIn(str(target / "scripts/repoecho_cli.py"), launcher.read_text())
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

    def test_project_install(self):
        with tempfile.TemporaryDirectory() as root:
            result = self.install("--project", root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((Path(root) / ".github/skills/repoecho/scripts/repoecho.py").is_file())


if __name__ == "__main__":
    unittest.main()
